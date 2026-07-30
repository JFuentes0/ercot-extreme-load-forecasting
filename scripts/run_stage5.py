"""Execute freeze stage 5 — the full leave-one-event-out sweep (D-015).

Authorized by **D-015**, which extends the real-data execution gate to stage 5 and
covers the content of stage 6 by running all three frozen seeds in one pass. The
analysis is pre-registered by **D-016** (`docs/track_a/ANALYSIS_PLAN_v1.md`) and
must be committed before this script runs.

Scope: every derived load-eligible fold × both arms × both feature sets (D-012) ×
both context conditions (D-013) × the three frozen seeds (freeze §8). Censoring
follows D-010; stopping follows D-014.

Built to run unattended, so it is defensive by construction:

* **Resumable.** A run whose manifest already exists is skipped. An interruption
  banks completed work; re-invoking continues rather than restarting.
* **Fail-soft per fold.** A fold that cannot be built is logged to a skip
  register and the sweep continues. The register is written to disk and must be
  reported alongside any result.
* **Refuse rather than guess.** Anything not settled in advance stops that fold
  and is recorded. No scientific choice is made while the PI is asleep.
* **Serial and single-process**, deliberately: available memory makes parallel
  sharding an OOM risk part-way through, and reliability beats speed here.

Usage:
    python scripts/run_stage5.py
    python scripts/run_stage5.py --limit-folds 2     # smoke test
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

import torch
import yaml

from ercot_forecasting.track_a.censoring import load_censoring_index
from ercot_forecasting.track_a.context_conditions import ContextCondition
from ercot_forecasting.track_a.event_eligibility import derive_eligible_events
from ercot_forecasting.track_a.features import build_episode_arrays
from ercot_forecasting.track_a.load_data import load_harmonized
from ercot_forecasting.track_a.partition import build_loeo_folds, build_target_days
from ercot_forecasting.track_a.stage4 import (
    Stage4Config,
    build_fold_dataset,
    build_fold_episodes,
    partition_fold_days,
    run_fold_arm,
    sha256_file,
    write_run_manifest,
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
ANALYSIS_PLAN = REPO / "docs" / "track_a" / "ANALYSIS_PLAN_v1.md"
RUNS = REPO / "runs" / "track_a" / "stage5"

ARMS = ("CNP", "AdaCNP")


def _manifest_path(
    feature_set: str, event_id: str, arm: str, condition: str, seed: int
) -> Path:
    return (
        RUNS
        / feature_set
        / f"run_manifest_{event_id}_{arm.lower()}_{condition}_seed{seed}.json"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit-folds",
        type=int,
        default=None,
        help="run only the first N folds (smoke test)",
    )
    args = parser.parse_args(argv)

    # The pre-registration must exist before any stage-5 data does. Refuse
    # otherwise: running first and writing the analysis plan afterwards would
    # make the result exploratory, which is the one failure this design exists
    # to prevent.
    if not ANALYSIS_PLAN.is_file():
        print(
            f"REFUSING: the pre-registered analysis plan is absent ({ANALYSIS_PLAN}). "
            "Stage 5 must not run before its analysis plan is committed.",
            file=sys.stderr,
        )
        return 2

    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    if plan["blocked_by"]:
        print(f"REFUSING: outstanding gates {plan['blocked_by']}", file=sys.stderr)
        return 2

    scaffold = load_scaffold_config(SCAFFOLD)
    seeds = [int(s) for s in plan["seeds"]]
    context_size = int(plan["context_size"])
    steps = int(plan["training_steps"])
    feature_sets = list(plan["feature_sets"])
    conditions = [ContextCondition(c) for c in plan["context_conditions"]]

    started = time.time()
    print("=== STAGE 5 — full leave-one-event-out sweep (D-015) ===")
    print(f"  analysis plan     {ANALYSIS_PLAN.relative_to(REPO)}  (pre-registered)")
    print(f"  seeds             {seeds}")
    print(f"  feature sets      {feature_sets}")
    print(f"  conditions        {[c.value for c in conditions]}")
    print(f"  training steps    {steps}   stopping on inner validation (D-014)")

    load = load_harmonized(LOAD, usable_only=True)
    eligible = derive_eligible_events(INVENTORY, LOAD)
    censoring = load_censoring_index(CENSORING)
    temperature = load_regional_temperature(TEMPERATURE)
    target_index = build_target_days(load)
    folds = list(build_loeo_folds(eligible))
    if args.limit_folds:
        folds = folds[: args.limit_folds]
        print(f"  SMOKE TEST: limited to {len(folds)} fold(s)")

    total = len(folds) * len(feature_sets) * len(conditions) * len(seeds) * len(ARMS)
    print(f"  derived folds     {len(eligible.event_ids)}  (derived, not a literal)")
    print(f"  planned runs      {total}")

    print("\n=== EPISODE CONSTRUCTION (once per feature set) ===")
    episodes = {}
    for name in feature_sets:
        temp = temperature if name == "temperature" else None
        arrays = build_episode_arrays(load, target_index, temperature=temp)
        episodes[name] = arrays
        print(
            f"  {name:<12} {len(arrays):>6} days, {arrays.x.shape[1]:>3} features, "
            f"{len(arrays.rejected)} rejected"
        )

    input_hashes = {
        "load": sha256_file(LOAD),
        "event_inventory": sha256_file(INVENTORY),
        "censoring": sha256_file(CENSORING),
        "temperature": sha256_file(TEMPERATURE),
    }
    config_sha256 = sha256_file(PLAN)

    skipped: list[dict] = []
    completed = 0
    reused = 0

    print(f"\n{'=' * 78}\n=== SWEEP ===")
    for feature_set in feature_sets:
        for condition in conditions:
            for seed in seeds:
                config = Stage4Config(
                    seed=seed,
                    context_size=context_size,
                    steps=steps,
                    context_condition=condition,
                )
                for fold in folds:
                    cell = f"{feature_set}/{condition.value}/seed{seed}"
                    wanted = [
                        _manifest_path(
                            feature_set, fold.event_id, arm, condition.value, seed
                        )
                        for arm in ARMS
                    ]
                    if all(p.is_file() for p in wanted):
                        reused += len(ARMS)
                        continue

                    try:
                        partition = partition_fold_days(load, fold, target_index)
                        dataset = build_fold_dataset(
                            load, partition, target_index, episodes[feature_set]
                        )
                        train_episodes, event_episodes = build_fold_episodes(
                            dataset, config, RUNS / feature_set
                        )
                        line = []
                        for arm, path in zip(ARMS, wanted, strict=True):
                            result = run_fold_arm(
                                arm,
                                scaffold,
                                dataset,
                                train_episodes,
                                event_episodes,
                                censoring,
                                config,
                            )
                            write_run_manifest(
                                path,
                                result,
                                config,
                                eligible,
                                censoring,
                                input_hashes,
                                config_sha256,
                                train_episodes.context_file.sha256,
                                extra={
                                    "stage": 5,
                                    "authorization": (
                                        "D-015 (stage 5 full LOEO; analysis "
                                        "pre-registered by D-016)"
                                    ),
                                    "feature_set": feature_set,
                                    "feature_dim": int(dataset.train.x.shape[1]),
                                    "context_condition": condition.value,
                                    "context_condition_description": (
                                        condition.description
                                    ),
                                },
                            )
                            completed += 1
                            line.append(f"{arm} {result.score.primary_nll:>8.4f}")
                        done = completed + reused
                        rate = (time.time() - started) / max(completed, 1)
                        eta = (total - done) * rate / 60.0
                        print(
                            f"  [{done:>3}/{total}] {cell:<32}{fold.event_id:<16}"
                            f"{'  '.join(line)}   eta {eta:>5.0f}m",
                            flush=True,
                        )
                    except Exception as error:  # noqa: BLE001 - unattended run
                        # Fail soft: log the fold, keep the sweep going. Halting
                        # here would mean waking to a stack trace and no results.
                        skipped.append(
                            {
                                "feature_set": feature_set,
                                "context_condition": condition.value,
                                "seed": seed,
                                "event_id": fold.event_id,
                                "error": f"{type(error).__name__}: {error}",
                                "traceback": traceback.format_exc(limit=6),
                            }
                        )
                        print(
                            f"  [SKIP] {cell:<32}{fold.event_id:<16}"
                            f"{type(error).__name__}: {error}",
                            file=sys.stderr,
                            flush=True,
                        )

    RUNS.mkdir(parents=True, exist_ok=True)
    register = RUNS / "skip_register.json"
    register.write_text(
        json.dumps(
            {
                "planned_runs": total,
                "completed_this_invocation": completed,
                "already_present_skipped": reused,
                "failed_folds": skipped,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    elapsed = (time.time() - started) / 60.0
    print(f"\n{'=' * 78}\n=== SWEEP COMPLETE ===")
    print(f"  planned runs            {total}")
    print(f"  completed now           {completed}")
    print(f"  already present         {reused}")
    print(f"  failed folds            {len(skipped)}")
    print(f"  elapsed                 {elapsed:.1f} min")
    print(f"  skip register           {register.relative_to(REPO)}")
    if skipped:
        print("\n  FOLDS SKIPPED — these MUST be reported with any result:")
        for entry in skipped:
            print(
                f"    {entry['feature_set']}/{entry['context_condition']}/"
                f"seed{entry['seed']} {entry['event_id']}: {entry['error']}"
            )
    print(f"\n  torch {torch.__version__}  device cpu")
    print("  Next: python scripts/analyze_stage5.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
