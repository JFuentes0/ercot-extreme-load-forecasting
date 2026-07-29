"""Execute stage-3 normal-period validation for both arms.

Authorized by decision **D-008**: freeze execution stage 3 only, verified real
data, **non-event periods only**, every event-period hour excluded.

This script produces no held-out-event prediction and inspects no event-period
model performance. Stage 4 remains blocked pending the censoring ruling.

Usage:
    python scripts/run_stage3.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import torch

from ercot_forecasting.track_a.stage3 import (
    EpisodeSet,
    Stage3Config,
    build_stage3_dataset,
    persist_context_indices,
    run_arm,
    select_context_indices,
    write_run_manifest,
)
from ercot_forecasting.track_a.train import load_scaffold_config

REPO = Path(__file__).resolve().parents[1]
INVENTORY = REPO / "data" / "shared" / "event_inventory_headline.csv"
LOAD = REPO / "data" / "frozen" / "track_a" / "ercot_hourly_load_harmonized.csv"
SCAFFOLD = REPO / "configs" / "track_a" / "scaffold_synthetic.yaml"
RUNS = REPO / "runs" / "track_a" / "stage3"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    scaffold = load_scaffold_config(SCAFFOLD)
    config = Stage3Config(
        seed=int(scaffold["seeds"][0]),
        context_size=int(scaffold["context_size_headline"]),
    )

    print("=== STAGE 3 — normal-period validation (D-008) ===")
    print(f"  seed          {config.seed}")
    print(f"  context size  {config.context_size}")

    dataset = build_stage3_dataset(INVENTORY, LOAD, config)
    print(f"  train episodes      {len(dataset.train):,}")
    print(f"  validation episodes {len(dataset.validation):,}")
    print(f"  train span          {dataset.train.days[0]} .. {dataset.train.days[-1]}")
    print(
        f"  validation span     {dataset.validation.days[0]} .. "
        f"{dataset.validation.days[-1]}"
    )

    print("\n=== CONTEXT SELECTION (inputs only, issuance-safe) ===")
    train_indices, train_rows = select_context_indices(
        dataset.train.days,
        dataset.train_x,
        dataset.train.days,
        dataset.train_x,
        config.context_size,
    )
    val_indices, val_rows = select_context_indices(
        dataset.validation.days,
        dataset.val_x,
        dataset.train.days,
        dataset.train_x,
        config.context_size,
    )
    train_days = tuple(dataset.train.days[i] for i in train_rows)
    val_days = tuple(dataset.validation.days[i] for i in val_rows)

    train_context = persist_context_indices(
        RUNS / "context_indices_train.csv",
        train_days,
        dataset.train.days,
        train_indices,
    )
    val_context = persist_context_indices(
        RUNS / "context_indices_validation.csv",
        val_days,
        dataset.train.days,
        val_indices,
    )
    train_episodes = EpisodeSet(train_days, train_rows, train_indices, train_context)
    val_episodes = EpisodeSet(val_days, val_rows, val_indices, val_context)

    dropped_train = len(dataset.train) - len(train_days)
    print(
        f"  train episodes kept     {len(train_days):,}  "
        f"(dropped {dropped_train} with too few issuance-safe candidates)"
    )
    print(f"  train context file      {train_context.sha256[:16]}")
    print(f"  validation episodes     {len(val_days):,}")
    print(f"  validation context file {val_context.sha256[:16]}")

    load_hash = sha256_of(LOAD)
    inventory_hash = sha256_of(INVENTORY)

    results = []
    for arm in ("CNP", "AdaCNP"):
        print(f"\n=== ARM: {arm} ===")
        result = run_arm(arm, scaffold, dataset, train_episodes, val_episodes, config)
        results.append(result)
        print(f"  trainable parameters  {result.trainable_parameters:,}")
        print(f"  output shape          {result.output_shape}")
        print(
            f"  train NLL             {result.initial_loss:.6f} -> "
            f"{result.final_loss:.6f}"
        )
        print(
            f"  validation NLL        {result.validation_nll:.6f}  "
            f"(normalized units, non-event days)"
        )
        print(f"  min predicted scale   {result.min_scale:.8f}")
        print(f"  max weight deviation  {result.max_weight_deviation:.3e}")
        manifest = write_run_manifest(
            RUNS / f"run_manifest_{arm.lower()}_seed{config.seed}.json",
            result,
            config,
            train_episodes,
            val_episodes,
            load_hash,
            inventory_hash,
        )
        print(f"  manifest              {manifest.relative_to(REPO)}")

    print("\n=== DETERMINISM (repeat CNP at the same seed) ===")
    repeat = run_arm("CNP", scaffold, dataset, train_episodes, val_episodes, config)
    identical = repeat.losses == results[0].losses
    print(f"  identical loss trace  {identical}")
    print(f"  final loss run 1      {results[0].final_loss:.12f}")
    print(f"  final loss run 2      {repeat.final_loss:.12f}")

    print("\n=== CONTEXT IDENTITY ACROSS ARMS ===")
    same = {r.context_file_sha256 for r in results}
    print(f"  both arms consumed    {len(same)} distinct context file(s)")
    print(f"  sha256                {results[0].context_file_sha256}")

    print("\n=== SCOPE ===")
    print("  held-out-event prediction : NONE")
    print("  event-period hours used   : 0 (excluded before episode construction)")
    print(f"  torch {torch.__version__}  device cpu")
    return 0


if __name__ == "__main__":
    sys.exit(main())
