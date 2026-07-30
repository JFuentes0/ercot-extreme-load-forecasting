"""Execute the stage-4 exploratory held-out-event grid for both arms.

Authorized by decision **D-011**, which extends the D-008 real-data execution
gate to freeze execution **stage 4 only**. Stages 5 and 6 remain blocked.

Every result produced here is **EXPLORATORY** (freeze §10) and may not be
reported as adjudicating the CNP-versus-AdaCNP hypothesis. Censoring follows the
adopted ruling **D-010**: ``verified_shed`` hours are excluded from the primary
latent-demand NLL, ``unresolved`` hours are retained and flagged, and the
all-hours served-load NLL is reported as a required diagnostic.

The run is a factorial over the replication-fidelity axes identified in
`docs/track_a/REPLICATION_FIDELITY_v1.md`:

* **feature set** — base (calendar + load lags) versus temperature (D-012);
* **context condition** — nearest-neighbour retrieval versus paper-faithful
  random sampling (D-013);
* **seed** — all three frozen seeds, so a spread can be reported (freeze §8).

Each cell runs both arms on each trio event. Because both arms share a cell's
persisted context indices and its normalizer, the **within-cell paired
difference** is the only quantity comparable across the grid.

Usage:
    python scripts/run_stage4.py
"""

from __future__ import annotations

import json
import statistics
import sys
from dataclasses import dataclass
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
    RESULT_LABEL,
    Stage4Config,
    Stage4Error,
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
RUNS = REPO / "runs" / "track_a" / "stage4"

ARMS = ("CNP", "AdaCNP")


@dataclass
class Row:
    """One executed run, flattened for the summary tables."""

    feature_set: str
    condition: str
    seed: int
    event_id: str
    arm: str
    primary_nll: float
    served_nll: float
    inner_val_nll: float
    selected_step: int
    excluded: int
    parameters: int


def main() -> int:
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    if int(plan["authorized_stage"]) < 4:
        print("REFUSING: the run plan does not authorize stage 4", file=sys.stderr)
        return 2
    if plan["blocked_by"]:
        print(f"REFUSING: outstanding gates {plan['blocked_by']}", file=sys.stderr)
        return 2

    scaffold = load_scaffold_config(SCAFFOLD)
    seeds = [int(s) for s in plan["seeds"]]
    context_size = int(plan["context_size"])
    steps = int(plan["training_steps"])
    feature_sets = list(plan["feature_sets"])
    conditions = [ContextCondition(c) for c in plan["context_conditions"]]
    planned_events = [entry["event_id"] for entry in plan["events"]]

    print("=== STAGE 4 — exploratory held-out-event grid (D-011) ===")
    print(f"  result label     {RESULT_LABEL}")
    print(f"  seeds            {seeds}")
    print(f"  context size     {context_size}")
    print(f"  training steps   {steps}  (stopping chosen on inner validation)")
    print(f"  feature sets     {feature_sets}")
    print(f"  conditions       {[c.value for c in conditions]}")
    print(f"  events           {', '.join(planned_events)}")
    print(
        f"  total runs       {len(feature_sets) * len(conditions) * len(seeds) * len(planned_events) * len(ARMS)}"
    )

    load = load_harmonized(LOAD, usable_only=True)
    eligible = derive_eligible_events(INVENTORY, LOAD)
    censoring = load_censoring_index(CENSORING)
    temperature = load_regional_temperature(TEMPERATURE)
    target_index = build_target_days(load)
    folds = {fold.event_id: fold for fold in build_loeo_folds(eligible)}

    missing = [e for e in planned_events if e not in folds]
    if missing:
        print(f"REFUSING: events absent or ineligible: {missing}", file=sys.stderr)
        return 2

    print("\n=== DERIVED INVENTORY ===")
    print(f"  eligible events / LOEO folds  {len(eligible.event_ids)}  (derived)")
    print(
        f"  censoring states              {censoring.n_verified_shed} verified_shed, "
        f"{censoring.n_unresolved} unresolved, "
        f"{censoring.n_verified_no_shed} verified_no_shed "
        f"over {censoring.total_event_hours} event-hours"
    )

    # Episode arrays are fold-independent: build each feature set once.
    print("\n=== EPISODE CONSTRUCTION (once per feature set) ===")
    episodes = {}
    for name in feature_sets:
        temp = temperature if name == "temperature" else None
        arrays = build_episode_arrays(load, target_index, temperature=temp)
        episodes[name] = arrays
        print(
            f"  {name:<12} {len(arrays):>6} days, {arrays.x.shape[1]:>3} features, "
            f"{len(arrays.rejected)} day(s) rejected"
        )

    input_hashes = {
        "load": sha256_file(LOAD),
        "event_inventory": sha256_file(INVENTORY),
        "censoring": sha256_file(CENSORING),
        "temperature": sha256_file(TEMPERATURE),
    }
    config_sha256 = sha256_file(PLAN)

    rows: list[Row] = []
    for feature_set in feature_sets:
        for condition in conditions:
            for seed in seeds:
                cell = f"{feature_set}/{condition.value}/seed{seed}"
                config = Stage4Config(
                    seed=seed,
                    context_size=context_size,
                    steps=steps,
                    context_condition=condition,
                )
                for event_id in planned_events:
                    partition = partition_fold_days(load, folds[event_id], target_index)
                    dataset = build_fold_dataset(
                        load, partition, target_index, episodes[feature_set]
                    )
                    train_episodes, event_episodes = build_fold_episodes(
                        dataset, config, RUNS / feature_set
                    )
                    for arm in ARMS:
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
                            RUNS
                            / feature_set
                            / f"run_manifest_{event_id}_{arm.lower()}"
                            f"_{condition.value}_seed{seed}.json",
                            result,
                            config,
                            eligible,
                            censoring,
                            input_hashes,
                            config_sha256,
                            train_episodes.context_file.sha256,
                            extra={
                                "feature_set": feature_set,
                                "feature_dim": int(dataset.train.x.shape[1]),
                                "context_condition": condition.value,
                                "context_condition_description": condition.description,
                            },
                        )
                        rows.append(
                            Row(
                                feature_set=feature_set,
                                condition=condition.value,
                                seed=seed,
                                event_id=event_id,
                                arm=arm,
                                primary_nll=result.score.primary_nll,
                                served_nll=result.score.served_load_nll,
                                inner_val_nll=result.inner_validation_nll,
                                selected_step=result.selected_step,
                                excluded=result.score.excluded_verified_shed_hours,
                                parameters=result.trainable_parameters,
                            )
                        )
                    print(
                        f"  {cell:<34}{event_id:<16}"
                        f"CNP {rows[-2].primary_nll:>8.4f}   "
                        f"AdaCNP {rows[-1].primary_nll:>8.4f}   "
                        f"delta {rows[-2].primary_nll - rows[-1].primary_nll:>+8.4f}"
                    )

    _report(rows)
    (RUNS / "stage4_grid_results.json").write_text(
        json.dumps([r.__dict__ for r in rows], indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n  grid results  {(RUNS / 'stage4_grid_results.json').relative_to(REPO)}")
    print(f"  torch {torch.__version__}  device cpu")
    return 0


def _report(rows: list[Row]) -> None:
    """Summarize the grid by cell, on paired within-cell differences only."""
    print(f"\n{'=' * 78}\n=== STAGE 4 SUMMARY — EXPLORATORY ===")
    print(
        "\nPaired CNP - AdaCNP primary-NLL difference, per cell.\n"
        "Positive => AdaCNP better (lower NLL). Each pair shares a normalizer and\n"
        "a context-index file, so only WITHIN-pair differences are comparable.\n"
    )
    header = (
        f"{'feature set':<13}{'context':<10}{'n pairs':>8}"
        f"{'mean delta':>12}{'sd':>9}{'AdaCNP wins':>13}"
    )
    print(header)
    print("-" * len(header))

    cells: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        if row.arm != "CNP":
            continue
        match = next(
            r
            for r in rows
            if r.arm == "AdaCNP"
            and (r.feature_set, r.condition, r.seed, r.event_id)
            == (row.feature_set, row.condition, row.seed, row.event_id)
        )
        cells.setdefault((row.feature_set, row.condition), []).append(
            row.primary_nll - match.primary_nll
        )

    for (feature_set, condition), deltas in cells.items():
        wins = sum(1 for d in deltas if d > 0)
        sd = statistics.stdev(deltas) if len(deltas) > 1 else float("nan")
        print(
            f"{feature_set:<13}{condition:<10}{len(deltas):>8}"
            f"{statistics.fmean(deltas):>12.4f}{sd:>9.4f}"
            f"{wins:>8}/{len(deltas):<4}"
        )

    print(
        "\nA mean difference smaller than its own spread is not a detected effect.\n"
        "Hu et al.'s own AdaCNP-over-CNP NLL margin is 0.8-3.4% with overlapping\n"
        "reported spreads, so a null here is consistent with the paper, not a\n"
        "refutation of it. See docs/track_a/REPLICATION_FIDELITY_v1.md."
    )

    print("\n=== DISCLOSURE (D-010 §3.5, mandatory) ===")
    print(
        "  EXPLORATORY. Primary metric excludes verified_shed hours (count per event\n"
        "  in each manifest). unresolved hours are retained and flagged; their\n"
        "  censoring status is unknown and is not resolved in either direction.\n"
        "  Served-load diagnostic reports a different estimand (served load, not\n"
        "  latent demand)."
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Stage4Error as error:
        print(f"STAGE 4 STOPPED: {error}", file=sys.stderr)
        sys.exit(1)
