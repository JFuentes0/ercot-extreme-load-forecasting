"""Aggregate non-event CNP-versus-AdaCNP comparison — the paper-comparable setting.

Authorized by **D-008**, which grants real-data execution for stage 3 restricted
to **non-event periods**. Every event-period hour is excluded before any episode
is built, so this script stays inside that grant: it produces no held-out-event
prediction and inspects no event-period performance.

Why this exists as a first-class result rather than a validation step. Hu et al.
evaluate AdaCNP on continuous PJM and ISO-NE series with a standard test split,
and report an AdaCNP-over-CNP NLL margin of 0.8–3.4%. Track A's *event-regime*
comparison rests on a handful of paired events, far too few to resolve a margin
that size. This aggregate comparison spans thousands of validation day-episodes
and is therefore the setting in which the paper's finding can actually be tested
on ERCOT data.

Grid: feature set × context condition × seed × arm, with both arms sharing each
cell's normalizer and persisted context indices, so the **within-cell paired
difference** is the comparable quantity.

Usage:
    python scripts/run_aggregate_comparison.py
"""

from __future__ import annotations

import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

import torch
import yaml

from ercot_forecasting.track_a.context_conditions import (
    ContextCondition,
    build_context_indices,
)
from ercot_forecasting.track_a.stage3 import (
    EpisodeSet,
    Stage3Config,
    build_stage3_dataset,
    persist_context_indices,
    run_arm,
)
from ercot_forecasting.track_a.stage4 import read_context_indices, sha256_file
from ercot_forecasting.track_a.train import load_scaffold_config
from ercot_forecasting.track_a.weather import load_regional_temperature

REPO = Path(__file__).resolve().parents[1]
INVENTORY = REPO / "data" / "shared" / "event_inventory_headline.csv"
LOAD = REPO / "data" / "frozen" / "track_a" / "ercot_hourly_load_harmonized.csv"
TEMPERATURE = REPO / "data" / "frozen" / "track_a" / "regional_index.parquet"
SCAFFOLD = REPO / "configs" / "track_a" / "scaffold_synthetic.yaml"
PLAN = REPO / "configs" / "track_a" / "exploratory_stage4_runs.yaml"
RUNS = REPO / "runs" / "track_a" / "aggregate"

ARMS = ("CNP", "AdaCNP")

#: Steps for the aggregate runs. Larger than the original 300: the aggregate
#: validation set is in-distribution, so unlike the event regime it does not
#: degrade with training (see D-014).
STEPS = 2000


@dataclass
class Row:
    feature_set: str
    condition: str
    seed: int
    arm: str
    validation_nll: float
    min_scale: float
    parameters: int
    train_episodes: int
    validation_episodes: int
    context_sha256: str


def main() -> int:
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    scaffold = load_scaffold_config(SCAFFOLD)
    seeds = [int(s) for s in plan["seeds"]]
    context_size = int(plan["context_size"])
    feature_sets = list(plan["feature_sets"])
    conditions = [ContextCondition(c) for c in plan["context_conditions"]]

    print("=== AGGREGATE NON-EVENT COMPARISON (D-008, stage 3 scope) ===")
    print(f"  seeds          {seeds}")
    print(f"  context size   {context_size}")
    print(f"  steps          {STEPS}")
    print(f"  feature sets   {feature_sets}")
    print(f"  conditions     {[c.value for c in conditions]}")
    print("  scope          NON-EVENT PERIODS ONLY; no held-out-event prediction")

    temperature = load_regional_temperature(TEMPERATURE)
    input_hashes = {
        "load": sha256_file(LOAD),
        "event_inventory": sha256_file(INVENTORY),
        "temperature": sha256_file(TEMPERATURE),
    }

    rows: list[Row] = []
    for feature_set in feature_sets:
        temp = temperature if feature_set == "temperature" else None
        for condition in conditions:
            for seed in seeds:
                config = Stage3Config(
                    seed=seed,
                    context_size=context_size,
                    steps=STEPS,
                    context_condition=condition,
                )
                dataset = build_stage3_dataset(INVENTORY, LOAD, config, temp)

                train_indices, train_kept = build_context_indices(
                    condition,
                    target_days=dataset.train.days,
                    target_x=dataset.train_x,
                    pool_days=dataset.train.days,
                    pool_x=dataset.train_x,
                    context_size=context_size,
                    seed=seed,
                )
                val_indices, val_kept = build_context_indices(
                    condition,
                    target_days=dataset.validation.days,
                    target_x=dataset.val_x,
                    pool_days=dataset.train.days,
                    pool_x=dataset.train_x,
                    context_size=context_size,
                    seed=seed + 1,
                )
                train_days = tuple(dataset.train.days[i] for i in train_kept)
                val_days = tuple(dataset.validation.days[i] for i in val_kept)

                stem = f"{feature_set}_{condition.value}_seed{seed}"
                train_file = persist_context_indices(
                    RUNS / f"context_train_{stem}.csv",
                    train_days,
                    dataset.train.days,
                    train_indices,
                )
                val_file = persist_context_indices(
                    RUNS / f"context_validation_{stem}.csv",
                    val_days,
                    dataset.train.days,
                    val_indices,
                )

                # Re-read from disk so both arms provably consume the same bytes
                # rather than two in-memory arrays that happen to agree.
                train_episodes = EpisodeSet(
                    days=train_days,
                    target_rows=train_kept,
                    context_indices=read_context_indices(train_file.path),
                    context_file=train_file,
                )
                val_episodes = EpisodeSet(
                    days=val_days,
                    target_rows=val_kept,
                    context_indices=read_context_indices(val_file.path),
                    context_file=val_file,
                )

                cell = f"{feature_set}/{condition.value}/seed{seed}"
                for arm in ARMS:
                    result = run_arm(
                        arm, scaffold, dataset, train_episodes, val_episodes, config
                    )
                    rows.append(
                        Row(
                            feature_set=feature_set,
                            condition=condition.value,
                            seed=seed,
                            arm=arm,
                            validation_nll=result.validation_nll,
                            min_scale=result.min_scale,
                            parameters=result.trainable_parameters,
                            train_episodes=len(train_episodes),
                            validation_episodes=len(val_episodes),
                            context_sha256=result.context_file_sha256,
                        )
                    )
                print(
                    f"  {cell:<36}CNP {rows[-2].validation_nll:>8.4f}   "
                    f"AdaCNP {rows[-1].validation_nll:>8.4f}   "
                    f"delta {rows[-2].validation_nll - rows[-1].validation_nll:>+8.4f}"
                    f"   ({rows[-1].validation_episodes} val episodes)"
                )

    _report(rows)
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "aggregate_results.json").write_text(
        json.dumps(
            {"input_artifact_sha256": input_hashes, "rows": [r.__dict__ for r in rows]},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n  results  {(RUNS / 'aggregate_results.json').relative_to(REPO)}")
    print(f"  torch {torch.__version__}  device cpu")
    print("\n  held-out-event prediction : NONE")
    print("  event-period hours used   : 0 (excluded before episode construction)")
    return 0


def _report(rows: list[Row]) -> None:
    print("\n=== AGGREGATE SUMMARY ===")
    print(
        "\nPaired CNP - AdaCNP validation-NLL difference, per cell.\n"
        "Positive => AdaCNP better. Each pair shares a normalizer and a\n"
        "context-index file, so only WITHIN-pair differences are comparable.\n"
    )
    header = (
        f"{'feature set':<13}{'context':<10}{'n seeds':>8}"
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
            and (r.feature_set, r.condition, r.seed)
            == (row.feature_set, row.condition, row.seed)
        )
        cells.setdefault((row.feature_set, row.condition), []).append(
            row.validation_nll - match.validation_nll
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
        "\nCompare against Hu et al.'s reported AdaCNP-over-CNP NLL margins:\n"
        "  PJM     -0.92 vs -0.89  (3.4%, spreads +/-3.4% and +/-3.8%)\n"
        "  ISO-NE  -1.33 vs -1.32  (0.8%, spreads +/-4.6% and +/-6.6%)\n"
        "Their margin is smaller than their own spread in both datasets, and no\n"
        "significance test is reported. See docs/track_a/REPLICATION_FIDELITY_v1.md."
    )


if __name__ == "__main__":
    sys.exit(main())
