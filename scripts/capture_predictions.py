"""Capture per-hour predictions for the exploratory presentation figures.

The run manifests record aggregate metrics, not per-hour predictions, so the
reliability diagram and the February-2021 case study cannot be built from them.
This script **re-runs exactly the runs those figures need** and writes every
prediction to disk, together with the full identity of the run that produced it —
cell, condition, seed, arm, event, config hash — so each figure is traceable to a
reproducible run.

It reuses `stage4.train_fold_arm`, the same training path the sweep used, rather
than reimplementing the loop. Training is deterministic under the frozen seed, so
a captured run reproduces the sweep's model for the same configuration.

**Two regimes, one model.** For each fold the trained model is evaluated on:

* **extreme** — that fold's held-out event days;
* **normal** — days from the same fold's inner-validation block that contain **no
  event hour at all**, from any event in the inventory.

Using one model for both regimes is deliberate. An earlier plan compared the LOEO
folds against a separately-trained chronological-split model, which would have
confounded regime with training partition. Here the model, its normalizer and its
context pool are identical across the two curves, and only the regime differs.

Nothing here feeds the pre-registered analysis (D-016). These outputs exist only
for exploratory figures.

Usage:
    python scripts/capture_predictions.py                    # all folds, primary cell
    python scripts/capture_predictions.py --event E14_20210212
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml

from ercot_forecasting.track_a.censoring import load_censoring_index
from ercot_forecasting.track_a.context_conditions import ContextCondition
from ercot_forecasting.track_a.event_eligibility import derive_eligible_events
from ercot_forecasting.track_a.features import build_episode_arrays
from ercot_forecasting.track_a.load_data import load_harmonized
from ercot_forecasting.track_a.partition import (
    build_loeo_folds,
    build_target_days,
    stage3_target_days,
)
from ercot_forecasting.track_a.stage4 import (
    Stage4Config,
    _inner_validation_split,
    build_fold_dataset,
    build_fold_episodes,
    partition_fold_days,
    sha256_file,
    train_fold_arm,
)
from ercot_forecasting.track_a.train import load_scaffold_config
from ercot_forecasting.track_a.weather import load_regional_temperature

REPO = Path(__file__).resolve().parents[1]
INVENTORY = REPO / "data" / "shared" / "event_inventory_headline.csv"
LOAD = REPO / "data" / "frozen" / "track_a" / "ercot_hourly_load_harmonized.csv"
CENSORING = REPO / "data" / "frozen" / "track_a" / "v7_demand_censored_v3.csv"
TEMPERATURE = REPO / "data" / "frozen" / "track_a" / "regional_index.parquet"
SCAFFOLD = REPO / "configs" / "track_a" / "scaffold_synthetic.yaml"
PLAN = REPO / "configs" / "track_a" / "exploratory_stage4_runs.yaml"
OUT = REPO / "runs" / "track_a" / "predictions"

#: Match the D-016 primary cell so the figures describe the pre-registered
#: configuration, even though the figures themselves are exploratory.
FEATURE_SET = "temperature"
CONDITION = ContextCondition.SAMPLED
ARM = "AdaCNP"

#: Cap on captured normal-period days per fold. The reliability curve needs a few
#: thousand hours, not the whole training block, and this keeps the file small.
MAX_NORMAL_DAYS = 40


def _rows_for(
    model: torch.nn.Module,
    dataset,
    episodes,
    rows: np.ndarray,
    hours: list[pd.DatetimeIndex],
    x_source: torch.Tensor,
    y_source: torch.Tensor,
    regime: str,
    event_id: str,
    censoring,
    eval_batch: int,
) -> list[dict]:
    """Predict on the given episode rows and flatten to per-hour records."""
    out: list[dict] = []
    y_std, y_mean = dataset.normalizer.y_std, dataset.normalizer.y_mean

    model.eval()
    with torch.no_grad():
        for start in range(0, len(rows), eval_batch):
            batch = rows[start : start + eval_batch]
            picked = torch.tensor(
                episodes.context_indices[batch],
                dtype=torch.long,
                device=torch.device("cpu"),
            )
            chosen = torch.tensor(
                episodes.target_rows[batch],
                dtype=torch.long,
                device=torch.device("cpu"),
            )
            prediction = model(
                dataset.train_x[picked],
                dataset.train_y[picked],
                x_source[chosen].unsqueeze(1),
            )
            target = y_source[chosen].unsqueeze(1).numpy()
            mean = prediction.mean.numpy()
            scale = prediction.scale.numpy()

            for local, row in enumerate(batch):
                stamps = hours[int(row)]
                shed = censoring.shed_mask(np.asarray(stamps))
                unres = censoring.unresolved_mask(np.asarray(stamps))
                for hour in range(target.shape[-1]):
                    out.append(
                        {
                            "regime": regime,
                            "event_id": event_id,
                            "ts_utc": str(stamps[hour]),
                            "hour_index": hour,
                            "y_norm": float(target[local, 0, hour]),
                            "mean_norm": float(mean[local, 0, hour]),
                            "scale_norm": float(scale[local, 0, hour]),
                            # Denormalized to MW: a grid audience reads megawatts,
                            # not standardized units.
                            "y_mw": float(target[local, 0, hour]) * y_std + y_mean,
                            "mean_mw": float(mean[local, 0, hour]) * y_std + y_mean,
                            "scale_mw": float(scale[local, 0, hour]) * y_std,
                            "verified_shed": bool(shed[hour]),
                            "unresolved": bool(unres[hour]),
                        }
                    )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", default=None, help="capture one fold only")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args(argv)

    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    seed = args.seed if args.seed is not None else int(plan["seeds"][0])
    config = Stage4Config(
        seed=seed,
        context_size=int(plan["context_size"]),
        steps=int(plan["training_steps"]),
        context_condition=CONDITION,
    )

    print("=== CAPTURE PER-HOUR PREDICTIONS (exploratory figures only) ===")
    print(f"  cell        {FEATURE_SET} / {CONDITION.value}   (D-016 primary cell)")
    print(f"  arm         {ARM}")
    print(f"  seed        {seed}")
    print(f"  steps       {config.steps}   stopping on inner validation (D-014)")

    load = load_harmonized(LOAD, usable_only=True)
    eligible = derive_eligible_events(INVENTORY, LOAD)
    censoring = load_censoring_index(CENSORING)
    temperature = load_regional_temperature(TEMPERATURE)
    index = build_target_days(load)
    episodes_all = build_episode_arrays(load, index, temperature=temperature)

    # Days containing no event hour from ANY inventory event -- the normal regime.
    non_event_index, _rejected = stage3_target_days(load, eligible)
    non_event_days = set(non_event_index.days)
    print(f"  non-event days available   {len(non_event_days):,}")

    folds = list(build_loeo_folds(eligible))
    if args.event:
        folds = [f for f in folds if f.event_id == args.event]
        if not folds:
            print(f"no such fold: {args.event}", file=sys.stderr)
            return 1

    started = time.time()
    records: list[dict] = []
    provenance: list[dict] = []

    for i, fold in enumerate(folds, start=1):
        partition = partition_fold_days(load, fold, index)
        dataset = build_fold_dataset(load, partition, index, episodes_all)
        train_episodes, event_episodes = build_fold_episodes(
            dataset, config, OUT / "ctx"
        )
        trained = train_fold_arm(
            ARM, load_scaffold_config(SCAFFOLD), dataset, train_episodes, config
        )

        # extreme: the fold's own held-out event days
        extreme = _rows_for(
            trained.model,
            dataset,
            event_episodes,
            np.arange(len(event_episodes)),
            [dataset.event_hours[int(r)] for r in range(len(dataset.event_hours))],
            dataset.event_x,
            dataset.event_y,
            "extreme",
            fold.event_id,
            censoring,
            config.eval_batch,
        )

        # normal: inner-validation days from the SAME model that contain no event hour
        _fit_rows, val_rows = _inner_validation_split(
            len(train_episodes), config.inner_validation_fraction
        )
        clean = np.array(
            [r for r in val_rows if train_episodes.days[int(r)] in non_event_days],
            dtype=np.int64,
        )[:MAX_NORMAL_DAYS]
        normal = _rows_for(
            trained.model,
            dataset,
            train_episodes,
            clean,
            [index.hours[d] for d in train_episodes.days],
            dataset.train_x,
            dataset.train_y,
            "normal",
            fold.event_id,
            censoring,
            config.eval_batch,
        )

        records.extend(extreme)
        records.extend(normal)
        provenance.append(
            {
                "event_id": fold.event_id,
                "feature_set": FEATURE_SET,
                "context_condition": CONDITION.value,
                "arm": ARM,
                "seed": seed,
                "steps": config.steps,
                "selected_step": trained.selected_step,
                "inner_validation_nll": trained.inner_validation_nll,
                "context_size": config.context_size,
                "held_out_days": len(event_episodes),
                "normal_days_captured": len(clean),
                "event_context_file_sha256": event_episodes.context_file.sha256,
                "train_context_file_sha256": train_episodes.context_file.sha256,
            }
        )
        print(
            f"  [{i}/{len(folds)}] {fold.event_id:<16} extreme {len(extreme):>5} h, "
            f"normal {len(normal):>5} h, selected step {trained.selected_step}",
            flush=True,
        )

    OUT.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(records)
    csv_path = OUT / "per_hour_predictions.csv"
    frame.to_csv(csv_path, index=False, lineterminator="\n")

    meta = {
        "purpose": "exploratory presentation figures only; not part of D-016",
        "generated_by": "scripts/capture_predictions.py",
        "cell": {"feature_set": FEATURE_SET, "context_condition": CONDITION.value},
        "arm": ARM,
        "seed": seed,
        "input_artifact_sha256": {
            "load": sha256_file(LOAD),
            "event_inventory": sha256_file(INVENTORY),
            "censoring": sha256_file(CENSORING),
            "temperature": sha256_file(TEMPERATURE),
        },
        "config_sha256": sha256_file(PLAN),
        "runs": provenance,
        "rows": len(frame),
        "elapsed_minutes": (time.time() - started) / 60.0,
    }
    (OUT / "per_hour_predictions_provenance.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    print(f"\n  rows written        {len(frame):,}")
    print(f"  extreme hours       {(frame['regime'] == 'extreme').sum():,}")
    print(f"  normal hours        {(frame['regime'] == 'normal').sum():,}")
    print(f"  predictions         {csv_path.relative_to(REPO)}")
    print(
        f"  provenance          {(OUT / 'per_hour_predictions_provenance.json').relative_to(REPO)}"
    )
    print(f"  elapsed             {(time.time() - started) / 60.0:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
