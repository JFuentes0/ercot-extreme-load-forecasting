"""Stage-3 normal-period validation (freeze §10 stage 3, decision D-008).

Scope, and the boundaries this module refuses to cross:

* Non-event periods **only**. Every event-period hour is excluded before any
  episode is built, and `tests/track_a/test_partition.py` asserts it.
* **No held-out-event prediction and no event-period performance.** The metric
  reported here is Gaussian NLL over *normal* days. Stage 4 is blocked until the
  censoring ruling is adopted; nothing here approaches it.
* Both arms consume a **single persisted context-index file**, so the context
  sets are byte-identical by construction rather than by coincidence (Track A
  rules; freeze §4).
* Normalization is fitted on the **training partition only** (Track A rules).
* Context selection uses target inputs ``x`` only and is issuance-safe: a
  candidate day qualifies only if all of its hours are complete before the
  target's 09:00 ``America/Chicago`` D−1 cutoff.

The split is chronological: earlier days train, later days validate. A random
split would let a model interpolate between neighbouring days and would not
resemble the operational task.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from ercot_forecasting.track_a.context_conditions import ContextCondition
from ercot_forecasting.track_a.event_eligibility import derive_eligible_events
from ercot_forecasting.track_a.features import (
    EpisodeArrays,
    Normalizer,
    build_episode_arrays,
)
from ercot_forecasting.track_a.load_data import load_harmonized
from ercot_forecasting.track_a.losses import gaussian_nll
from ercot_forecasting.track_a.partition import stage3_target_days
from ercot_forecasting.track_a.train import (
    CPU,
    build_arm_model,
    seeded_generator,
)
from ercot_forecasting.track_a.weather import RegionalTemperature

#: A candidate context day must end before the target's issuance cutoff. Since
#: the cutoff is 09:00 local on D-1 and a day's last hour begins at 23:00 local,
#: the newest admissible candidate is D-2.
MIN_CONTEXT_LAG_DAYS = 2


@dataclass(frozen=True)
class Stage3Config:
    """Stage-3 run settings."""

    seed: int
    context_size: int
    train_fraction: float = 0.8
    steps: int = 300
    batch_size: int = 32
    learning_rate: float = 1.0e-3
    eval_batch: int = 256
    #: How the context set is drawn (D-013). ``NEAREST`` is the original
    #: behaviour; ``SAMPLED`` is faithful to Hu et al.
    context_condition: ContextCondition = ContextCondition.NEAREST


@dataclass(frozen=True)
class ContextIndexFile:
    """A persisted context-index selection, shared by both arms."""

    path: Path
    sha256: str
    n_episodes: int
    context_size: int
    indices: np.ndarray = field(repr=False)
    target_positions: np.ndarray = field(repr=False)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class Stage3Dataset:
    """Train and validation episodes with a training-fitted normalizer."""

    train: EpisodeArrays
    validation: EpisodeArrays
    normalizer: Normalizer
    train_x: torch.Tensor
    train_y: torch.Tensor
    val_x: torch.Tensor
    val_y: torch.Tensor


def build_stage3_dataset(
    inventory_path: str | Path,
    load_path: str | Path,
    config: Stage3Config,
    temperature: RegionalTemperature | None = None,
) -> Stage3Dataset:
    """Assemble non-event episodes, split chronologically, and normalize.

    Passing ``temperature`` adds the D-012 temperature block. Every
    event-period hour is excluded before any episode is built, whichever feature
    set is used, so the D-008 stage-3 restriction is unaffected.
    """
    load = load_harmonized(load_path, usable_only=True)
    eligible = derive_eligible_events(inventory_path, load_path)
    usable, _rejected = stage3_target_days(load, eligible)

    arrays = build_episode_arrays(load, usable, temperature=temperature)
    split = int(len(arrays) * config.train_fraction)
    if split < 1 or split >= len(arrays):
        raise ValueError("train_fraction produces an empty split")

    train = EpisodeArrays(
        days=arrays.days[:split],
        x=arrays.x[:split],
        y=arrays.y[:split],
        cutoffs=arrays.cutoffs[:split],
    )
    validation = EpisodeArrays(
        days=arrays.days[split:],
        x=arrays.x[split:],
        y=arrays.y[split:],
        cutoffs=arrays.cutoffs[split:],
    )

    normalizer = Normalizer.fit(train.x, train.y)
    return Stage3Dataset(
        train=train,
        validation=validation,
        normalizer=normalizer,
        train_x=torch.tensor(
            normalizer.transform_x(train.x), dtype=torch.float32, device=CPU
        ),
        train_y=torch.tensor(
            normalizer.transform_y(train.y), dtype=torch.float32, device=CPU
        ),
        val_x=torch.tensor(
            normalizer.transform_x(validation.x), dtype=torch.float32, device=CPU
        ),
        val_y=torch.tensor(
            normalizer.transform_y(validation.y), dtype=torch.float32, device=CPU
        ),
    )


def select_context_indices(
    target_days: tuple[date, ...],
    target_x: torch.Tensor,
    pool_days: tuple[date, ...],
    pool_x: torch.Tensor,
    context_size: int,
    chunk: int = 256,
) -> tuple[np.ndarray, np.ndarray]:
    """Nearest-in-input-space context, restricted to issuance-safe candidates.

    Selection reads target and candidate **inputs only**. Outcomes never enter,
    so this path is structurally incapable of target-``y`` leakage.

    The earliest targets in the record have fewer than ``context_size`` days
    preceding them and therefore cannot form a full context set. They are
    **dropped**, not padded and not back-filled from later days -- either would
    breach the issuance cutoff. Returns the selected indices for the surviving
    targets and their positions in ``target_days``.
    """
    pool_array = np.array(pool_days)
    rows: list[np.ndarray] = []
    kept: list[int] = []

    for start in range(0, len(target_days), chunk):
        stop = min(start + chunk, len(target_days))
        distance = torch.cdist(target_x[start:stop], pool_x, p=2.0)

        for row, position in enumerate(range(start, stop)):
            latest = target_days[position] - timedelta(days=MIN_CONTEXT_LAG_DAYS)
            admissible = int(np.searchsorted(pool_array, latest, side="right"))
            if admissible < context_size:
                continue
            row_distance = distance[row].clone()
            row_distance[admissible:] = float("inf")
            rows.append(
                torch.topk(row_distance, k=context_size, largest=False)
                .indices.cpu()
                .numpy()
            )
            kept.append(position)

    if not kept:
        raise ValueError("no target had enough issuance-safe context candidates")
    return np.vstack(rows), np.array(kept, dtype=np.int64)


def persist_context_indices(
    path: str | Path,
    target_days: tuple[date, ...],
    pool_days: tuple[date, ...],
    indices: np.ndarray,
) -> ContextIndexFile:
    """Write the selection to disk so both arms consume identical bytes.

    Context IDs are recorded for every episode (Track A rules).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    frame = pd.DataFrame(
        {
            "target_day": [str(d) for d in target_days],
            "context_days": [
                ",".join(str(pool_days[i]) for i in row) for row in indices
            ],
            "context_positions": [
                ",".join(str(int(i)) for i in row) for row in indices
            ],
        }
    )
    frame.to_csv(path, index=False, lineterminator="\n")

    return ContextIndexFile(
        path=path,
        sha256=_sha256(path),
        n_episodes=len(target_days),
        context_size=indices.shape[1],
        indices=indices,
        target_positions=np.arange(len(target_days)),
    )


@dataclass(frozen=True)
class EpisodeSet:
    """Episodes whose context has been selected and persisted.

    ``target_rows`` maps each episode to its row in the underlying arrays, so
    dropping early targets never misaligns an episode from its context.
    """

    days: tuple[date, ...]
    target_rows: np.ndarray
    context_indices: np.ndarray
    context_file: ContextIndexFile

    def __len__(self) -> int:
        return len(self.days)


def _episode_tensors(
    episodes: EpisodeSet,
    target_x: torch.Tensor,
    target_y: torch.Tensor,
    pool_x: torch.Tensor,
    pool_y: torch.Tensor,
    batch: np.ndarray,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    picked = torch.tensor(episodes.context_indices[batch], dtype=torch.long, device=CPU)
    chosen = torch.tensor(episodes.target_rows[batch], dtype=torch.long, device=CPU)
    return (
        pool_x[picked],
        pool_y[picked],
        target_x[chosen].unsqueeze(1),
        target_y[chosen].unsqueeze(1),
    )


@dataclass
class ArmResult:
    """Outcome of one arm's stage-3 run."""

    arm: str
    trainable_parameters: int
    losses: list[float]
    initial_loss: float
    final_loss: float
    validation_nll: float
    min_scale: float
    max_weight_deviation: float
    context_file_sha256: str
    output_shape: tuple[int, ...]


def _count_parameters(model: torch.nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def run_arm(
    arm: str,
    scaffold_config: dict[str, Any],
    dataset: Stage3Dataset,
    train_episodes: EpisodeSet,
    val_episodes: EpisodeSet,
    config: Stage3Config,
) -> ArmResult:
    """Train one arm on non-event days and evaluate on non-event validation."""
    model = build_arm_model(
        arm, scaffold_config, dataset.train.x.shape[1], config.seed
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    generator = seeded_generator(config.seed)
    n_train = len(train_episodes)

    model.train()
    losses: list[float] = []
    for _ in range(config.steps):
        rows = torch.randint(
            0, n_train, (config.batch_size,), generator=generator
        ).numpy()
        cx, cy, tx, ty = _episode_tensors(
            train_episodes,
            dataset.train_x,
            dataset.train_y,
            dataset.train_x,
            dataset.train_y,
            rows,
        )
        prediction = model(cx, cy, tx)
        loss = gaussian_nll(ty, prediction.mean, prediction.scale)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))

    model.eval()
    total, count = 0.0, 0
    min_scale = float("inf")
    max_weight_deviation = 0.0
    shape: tuple[int, ...] = ()
    with torch.no_grad():
        for start in range(0, len(val_episodes), config.eval_batch):
            rows = np.arange(start, min(start + config.eval_batch, len(val_episodes)))
            cx, cy, tx, ty = _episode_tensors(
                val_episodes,
                dataset.val_x,
                dataset.val_y,
                dataset.train_x,
                dataset.train_y,
                rows,
            )
            prediction = model(cx, cy, tx)
            shape = tuple(prediction.mean.shape)
            total += float(
                gaussian_nll(ty, prediction.mean, prediction.scale, reduction="sum")
            )
            count += ty.numel()
            min_scale = min(min_scale, float(prediction.scale.min()))
            totals = prediction.weights.sum(dim=-1)
            max_weight_deviation = max(
                max_weight_deviation,
                float((totals - 1.0).abs().max()),
            )

    return ArmResult(
        arm=arm,
        trainable_parameters=_count_parameters(model),
        losses=losses,
        initial_loss=losses[0],
        final_loss=losses[-1],
        validation_nll=total / count,
        min_scale=min_scale,
        max_weight_deviation=max_weight_deviation,
        context_file_sha256=val_episodes.context_file.sha256,
        output_shape=shape,
    )


def write_run_manifest(
    path: str | Path,
    arm: ArmResult,
    config: Stage3Config,
    train_episodes: EpisodeSet,
    val_episodes: EpisodeSet,
    load_sha256: str,
    inventory_sha256: str,
) -> Path:
    """Emit the per-run manifest the readiness contract requires."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "stage": 3,
        "authorization": "D-008 (stage 3 only, non-event periods)",
        "arm": arm.arm,
        "seed": config.seed,
        "context_size": config.context_size,
        "trainable_parameters": arm.trainable_parameters,
        "train_episodes": len(train_episodes),
        "validation_episodes": len(val_episodes),
        "train_days": [
            str(train_episodes.days[0]),
            str(train_episodes.days[-1]),
        ],
        "validation_days": [
            str(val_episodes.days[0]),
            str(val_episodes.days[-1]),
        ],
        "input_artifact_sha256": {
            "load": load_sha256,
            "event_inventory": inventory_sha256,
        },
        "context_index_file_sha256": {
            "train": train_episodes.context_file.sha256,
            "validation": val_episodes.context_file.sha256,
        },
        "normalization_fitted_on": "training partition only",
        "validation_gaussian_nll_normalized_units": arm.validation_nll,
        "min_predicted_scale": arm.min_scale,
        "max_weight_sum_deviation": arm.max_weight_deviation,
        "output_shape": list(arm.output_shape),
        "held_out_event_prediction": False,
        "event_period_hours_included": 0,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
