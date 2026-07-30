"""Stage-4 exploratory held-out-event experiment (freeze §10 stage 4, D-011).

Authorized by **D-011**, which extends the D-008 real-data execution gate to
stage 4 and to no further stage. Every result this module produces is
**EXPLORATORY** (freeze §10) and may not be reported as adjudicating the
CNP-versus-AdaCNP hypothesis.

Structural protections carried from the freeze, none of them optional:

* **Leave-one-event-out.** One fold per held-out event, derived from the
  imported inventory. No fold count appears as a literal (D-006, freeze §10.1).
* **±7-day buffer excluded from training *and* retrieval** (freeze §3). A
  training day is admissible only if its target hours **and its 24-hour lag
  window** lie entirely outside the buffered window — a day just past the buffer
  edge would otherwise carry held-out hours in through its own features.
* **Both arms consume one persisted context-index file**, re-read from disk for
  each arm so byte-identity is established by the file rather than assumed.
* **Normalization is fitted on the fold's training partition only.**
* **Issuance safety.** Context candidates and lag features are restricted to
  information complete before 09:00 ``America/Chicago`` on D−1 (D-007).

Censoring follows the adopted ruling (**D-010**,
`docs/track_a/CENSORING_TREATMENT_RULING_v1.md`):

* the primary latent-demand NLL **excludes** ``verified_shed`` hours;
* ``unresolved`` hours are **retained and flagged**, never defaulted;
* an all-hours **served-load** NLL is reported as a **required** diagnostic,
  whose estimand is served load rather than latent demand.

One limitation is disclosed rather than silently accepted: a held-out target
day's own lag features are drawn from observed served load, which for later days
of an event may include ``verified_shed`` hours. That is operationally correct —
a forecaster at issuance sees metered load, not latent demand — but it means
censored values enter the *inputs* even where D-010 removes them from the
*metric*. The ruling governs the metric; this note records the input side.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from ercot_forecasting.track_a.censoring import CensoringIndex
from ercot_forecasting.track_a.context_conditions import (
    ContextCondition,
    build_context_indices,
)
from ercot_forecasting.track_a.event_eligibility import EligibleEvents
from ercot_forecasting.track_a.features import (
    FEATURE_DIM,
    FEATURE_DIM_WITH_TEMPERATURE,
    LAG_HOURS,
    TEMP_LAG_HOURS,
    EpisodeArrays,
    Normalizer,
    build_episode_arrays,
)
from ercot_forecasting.track_a.load_data import CALENDAR_ZONE
from ercot_forecasting.track_a.losses import gaussian_nll
from ercot_forecasting.track_a.metrics import (
    COLD_CONTEXT_QUANTILE,
    HIGH_LOAD_QUANTILE,
    SecondaryMetrics,
    summarize,
)
from ercot_forecasting.track_a.partition import (
    BUFFER_DAYS,
    HORIZON,
    Fold,
    TargetDayIndex,
    build_target_days,
    issuance_cutoff_utc,
)
from ercot_forecasting.track_a.stage3 import (
    EpisodeSet,
    persist_context_indices,
)
from ercot_forecasting.track_a.train import (
    CPU,
    build_arm_model,
    seeded_generator,
)

#: The label every stage-4 result must carry (freeze §10).
RESULT_LABEL = "EXPLORATORY"

#: The governing censoring decision, named in every stage-4 manifest.
CENSORING_TREATMENT = "D-010 CENSORING_TREATMENT_RULING_v1"


def episode_lag_start(day: date, zone: str = CALENDAR_ZONE) -> pd.Timestamp:
    """The earliest hour that can enter a target day's lag features.

    The lag is the ``LAG_HOURS`` complete observations preceding the issuance
    cutoff (``features.build_episode_arrays``), so the earliest hour consumed is
    ``cutoff − LAG_HOURS``.

    **This must be derived from the cutoff, not from the day's own first hour.**
    The cutoff is 09:00 ``America/Chicago`` on D−1 — about 15 hours before the
    target day begins — so a span measured back from the first hour understates
    the true reach by that much and admits training days whose features draw on
    the held-out buffered window. An earlier revision made exactly that error.
    """
    return issuance_cutoff_utc(day, zone) - pd.Timedelta(hours=LAG_HOURS)


class Stage4Error(ValueError):
    """Raised when a stage-4 invariant cannot be satisfied."""


@dataclass(frozen=True)
class Stage4Config:
    """Stage-4 run settings. Frozen controls come from the freeze, not here."""

    seed: int
    context_size: int
    steps: int = 3000
    batch_size: int = 32
    learning_rate: float = 1.0e-3
    eval_batch: int = 256
    context_condition: ContextCondition = ContextCondition.NEAREST
    #: Latest chronological share of training episodes reserved to choose the
    #: stopping point. Never the held-out event — that would be leakage.
    inner_validation_fraction: float = 0.1
    #: Steps between inner-validation evaluations.
    eval_every: int = 100


@dataclass(frozen=True)
class FoldPartition:
    """Training and held-out day sets for one leave-one-event-out fold."""

    fold: Fold
    train_days: tuple[date, ...]
    event_days: tuple[date, ...]
    excluded_days: tuple[date, ...]

    def __post_init__(self) -> None:
        overlap = set(self.train_days) & set(self.event_days)
        if overlap:
            raise Stage4Error(
                f"fold {self.fold.event_id}: {len(overlap)} days appear in both "
                "training and the held-out event"
            )


def partition_fold_days(
    load: pd.DataFrame,
    fold: Fold,
    target_index: TargetDayIndex | None = None,
) -> FoldPartition:
    """Split usable target days into training, held-out, and excluded sets.

    A day is **held out** if any of its hours falls inside the event's own
    window. A day is **admissible for training** only if neither its hours nor
    its 24-hour lag window intersects the buffered window (freeze §3). Days that
    are neither — those inside the buffer but outside the event — are excluded
    from both, which is what the buffer is for.
    """
    index = target_index if target_index is not None else build_target_days(load)

    train: list[date] = []
    event: list[date] = []
    excluded: list[date] = []

    for day in index.days:
        hours = index.hours[day]
        first, last = hours.min(), hours.max()

        if (first <= fold.recovery) and (last >= fold.onset):
            event.append(day)
            continue

        # The lag window ends at the issuance cutoff, which precedes the day by
        # more than the lag length itself — see episode_lag_start.
        span_lo = episode_lag_start(day)
        if (span_lo <= fold.buffer_hi) and (last >= fold.buffer_lo):
            excluded.append(day)
            continue

        train.append(day)

    if not event:
        raise Stage4Error(
            f"fold {fold.event_id}: no complete 24-hour day overlaps the event window"
        )
    if not train:
        raise Stage4Error(f"fold {fold.event_id}: no admissible training day")

    return FoldPartition(
        fold=fold,
        train_days=tuple(train),
        event_days=tuple(event),
        excluded_days=tuple(excluded),
    )


@dataclass(frozen=True)
class FoldDataset:
    """Normalized tensors for one fold, fitted on its training partition only."""

    partition: FoldPartition
    train: EpisodeArrays
    event: EpisodeArrays
    normalizer: Normalizer
    train_x: torch.Tensor
    train_y: torch.Tensor
    event_x: torch.Tensor
    event_y: torch.Tensor
    event_hours: tuple[pd.DatetimeIndex, ...] = field(repr=False)
    #: `roll24` at each TRAINING day's issuance cutoff, aligned with
    #: ``train.days``. Supplies the cold-context-day metric (freeze §7); None
    #: for the base feature set, where the metric is undefined rather than zero.
    roll24_at_cutoff: np.ndarray | None = field(default=None, repr=False)


def build_fold_dataset(
    load: pd.DataFrame,
    partition: FoldPartition,
    target_index: TargetDayIndex | None = None,
    episodes: EpisodeArrays | None = None,
) -> FoldDataset:
    """Build episodes for a fold and normalize on its training partition.

    Pass ``episodes`` — the arrays for **every** usable day, built once — to
    avoid rebuilding them per fold. A day's features and target depend only on
    the load frame, so the per-fold rebuild recomputes identical values; only
    the normalizer is fold-specific. The argument is optional so callers that
    only need one fold stay simple.
    """
    index = target_index if target_index is not None else build_target_days(load)
    if episodes is None:
        episodes = build_episode_arrays(load, index)

    # A day with no episode row (its lag window was incomplete) cannot be used.
    available = set(episodes.days)
    train_days = tuple(d for d in partition.train_days if d in available)
    event_days = tuple(d for d in partition.event_days if d in available)
    if not train_days:
        raise Stage4Error(
            f"fold {partition.fold.event_id}: no training day has a complete episode"
        )
    if not event_days:
        raise Stage4Error(
            f"fold {partition.fold.event_id}: no held-out day has a complete episode"
        )

    train = episodes.select(train_days)
    event = episodes.select(event_days)

    normalizer = Normalizer.fit(train.x, train.y)
    return FoldDataset(
        partition=partition,
        train=train,
        event=event,
        normalizer=normalizer,
        train_x=torch.tensor(
            normalizer.transform_x(train.x), dtype=torch.float32, device=CPU
        ),
        train_y=torch.tensor(
            normalizer.transform_y(train.y), dtype=torch.float32, device=CPU
        ),
        event_x=torch.tensor(
            normalizer.transform_x(event.x), dtype=torch.float32, device=CPU
        ),
        event_y=torch.tensor(
            normalizer.transform_y(event.y), dtype=torch.float32, device=CPU
        ),
        event_hours=tuple(index.hours[d] for d in event.days),
        roll24_at_cutoff=_roll24_column(train),
    )


def _roll24_column(train: EpisodeArrays) -> np.ndarray | None:
    """Extract `roll24` at cutoff from a training day's feature vector.

    The temperature block lays out as calendar, load lags, temperature lags,
    then the derived terms with ``roll24_at_cutoff`` first — so it sits at a
    known offset and needs no separate plumbing. Returns None for the base
    feature set, which has no temperature columns at all.
    """
    if train.x.shape[1] != FEATURE_DIM_WITH_TEMPERATURE:
        return None
    return train.x[:, FEATURE_DIM + TEMP_LAG_HOURS].copy()


def read_context_indices(path: str | Path) -> np.ndarray:
    """Re-read a persisted context-index file into its integer selection.

    Both arms load their contexts through this function, so their context sets
    are identical because they came from the same bytes on disk, not because the
    code happened to construct them the same way twice.
    """
    frame = pd.read_csv(path)
    return np.vstack(
        [
            np.fromstring(row, dtype=np.int64, sep=",")
            for row in frame["context_positions"]
        ]
    )


def build_fold_episodes(
    dataset: FoldDataset,
    config: Stage4Config,
    context_dir: str | Path,
) -> tuple[EpisodeSet, EpisodeSet]:
    """Select and persist context indices for training and held-out episodes.

    Retrieval draws only from the fold's admissible training pool, so a context
    day can never come from inside the held-out event or its buffer.
    """
    context_dir = Path(context_dir)
    event_id = dataset.partition.fold.event_id
    suffix = f"_{config.context_condition.value}"

    train_indices, train_kept = build_context_indices(
        config.context_condition,
        target_days=dataset.train.days,
        target_x=dataset.train_x,
        pool_days=dataset.train.days,
        pool_x=dataset.train_x,
        context_size=config.context_size,
        seed=config.seed,
    )
    train_days = tuple(dataset.train.days[i] for i in train_kept)
    train_file = persist_context_indices(
        context_dir / f"context_indices_train_{event_id}{suffix}.csv",
        train_days,
        dataset.train.days,
        train_indices,
    )

    event_indices, event_kept = build_context_indices(
        config.context_condition,
        target_days=dataset.event.days,
        target_x=dataset.event_x,
        pool_days=dataset.train.days,
        pool_x=dataset.train_x,
        context_size=config.context_size,
        # Offsetting keeps the held-out draw from mirroring the training draw
        # index-for-index while remaining fully determined by the frozen seed.
        seed=config.seed + 1,
    )
    if len(event_kept) != len(dataset.event.days):
        raise Stage4Error(
            f"fold {event_id}: {len(dataset.event.days) - len(event_kept)} held-out "
            "day(s) lacked a full issuance-safe context set"
        )
    event_days = tuple(dataset.event.days[i] for i in event_kept)
    event_file = persist_context_indices(
        context_dir / f"context_indices_event_{event_id}{suffix}.csv",
        event_days,
        dataset.train.days,
        event_indices,
    )

    train_set = EpisodeSet(
        days=train_days,
        target_rows=train_kept,
        context_indices=read_context_indices(train_file.path),
        context_file=train_file,
    )
    event_set = EpisodeSet(
        days=event_days,
        target_rows=event_kept,
        context_indices=read_context_indices(event_file.path),
        context_file=event_file,
    )
    _assert_retrieval_excludes_holdout(train_set, dataset)
    _assert_retrieval_excludes_holdout(event_set, dataset)
    return train_set, event_set


def _assert_retrieval_excludes_holdout(
    episodes: EpisodeSet, dataset: FoldDataset
) -> None:
    """Fail if any selected context day falls inside the held-out window."""
    fold = dataset.partition.fold
    pool = dataset.train.days
    for row in episodes.context_indices:
        for position in row:
            day = pool[int(position)]
            if fold.buffer_lo.date() <= day <= fold.buffer_hi.date():
                raise Stage4Error(
                    f"fold {fold.event_id}: context day {day} lies inside the "
                    "held-out buffered window"
                )


@dataclass(frozen=True)
class CensoredScore:
    """Held-out-event scores under the adopted D-010 treatment.

    ``secondary`` carries the freeze §7 metrics, computed over the *same* scored
    hours as the primary metric so they describe the same estimand. They are
    descriptive: freeze §7 states they do not adjudicate the comparison.
    """

    primary_nll: float
    served_load_nll: float
    scored_hours: int
    excluded_verified_shed_hours: int
    retained_unresolved_hours: int
    total_hours: int
    min_scale: float
    secondary: SecondaryMetrics | None = None

    @property
    def excluded_fraction(self) -> float:
        return self.excluded_verified_shed_hours / self.total_hours


def cold_context_mask(
    dataset: FoldDataset,
    episodes: EpisodeSet,
    rows: np.ndarray,
) -> np.ndarray | None:
    """Mark which of each episode's context days are cold (freeze §7, D-012).

    "Cold" is defined per fold, as a context day whose cutoff `roll24` falls
    below the ``COLD_CONTEXT_QUANTILE`` of the fold's own training pool — a
    relative definition, so no absolute temperature is hard-coded and the metric
    travels to a different record unchanged.

    Returns ``None`` for the base feature set, where no temperature column
    exists and the metric is genuinely undefined rather than zero.
    """
    if dataset.roll24_at_cutoff is None:
        return None
    pool = dataset.roll24_at_cutoff
    threshold = float(np.quantile(pool, COLD_CONTEXT_QUANTILE))
    picked = episodes.context_indices[rows]
    return (pool[picked] < threshold).astype(np.float64)


def score_held_out_event(
    model: torch.nn.Module,
    dataset: FoldDataset,
    episodes: EpisodeSet,
    censoring: CensoringIndex,
    config: Stage4Config,
) -> CensoredScore:
    """Score the held-out event under D-010.

    Returns the primary latent-demand NLL with ``verified_shed`` hours excluded,
    and the all-hours served-load NLL required as a secondary diagnostic. Both
    are in normalized units, matching the stage-3 convention.
    """
    hours_by_day = {
        day: dataset.event_hours[int(row)]
        for day, row in zip(episodes.days, episodes.target_rows, strict=True)
    }

    model.eval()
    shed_total, all_total = 0.0, 0.0
    shed_count, all_count = 0, 0
    excluded, unresolved = 0, 0
    min_scale = float("inf")

    # Collected over the SCORED hours only, so the secondary metrics describe
    # the same estimand as the primary (freeze §7, D-010).
    kept_target: list[np.ndarray] = []
    kept_mean: list[np.ndarray] = []
    kept_scale: list[np.ndarray] = []
    kept_weights: list[np.ndarray] = []
    kept_cold: list[np.ndarray] = []

    # The high-load threshold comes from the fold's TRAINING partition, never
    # from the held-out event -- deriving it from the data being scored would
    # leak the very tail behaviour the metric is meant to probe.
    high_load_threshold = float(
        np.quantile(dataset.train_y.numpy(), HIGH_LOAD_QUANTILE)
    )

    with torch.no_grad():
        for start in range(0, len(episodes), config.eval_batch):
            rows = np.arange(start, min(start + config.eval_batch, len(episodes)))
            picked = torch.tensor(
                episodes.context_indices[rows], dtype=torch.long, device=CPU
            )
            chosen = torch.tensor(
                episodes.target_rows[rows], dtype=torch.long, device=CPU
            )
            context_x = dataset.train_x[picked]
            context_y = dataset.train_y[picked]
            target_x = dataset.event_x[chosen].unsqueeze(1)
            target_y = dataset.event_y[chosen].unsqueeze(1)

            prediction = model(context_x, context_y, target_x)
            elementwise = gaussian_nll(
                target_y, prediction.mean, prediction.scale, reduction="none"
            )
            min_scale = min(min_scale, float(prediction.scale.min()))

            stamps = np.concatenate(
                [np.asarray(hours_by_day[episodes.days[r]]) for r in rows]
            )
            shed = censoring.shed_mask(stamps).reshape(len(rows), 1, HORIZON)
            unresolved += int(censoring.unresolved_mask(stamps).sum())

            values = elementwise.numpy()
            all_total += float(values.sum())
            all_count += values.size
            shed_total += float(values[~shed].sum())
            shed_count += int((~shed).sum())
            excluded += int(shed.sum())

            keep = ~shed
            kept_target.append(target_y.numpy()[keep])
            kept_mean.append(prediction.mean.numpy()[keep])
            kept_scale.append(prediction.scale.numpy()[keep])

            # Context weights are per-episode, not per-hour, so an episode is
            # included whenever any of its hours survived the exclusion.
            episode_kept = keep.reshape(len(rows), -1).any(axis=1)
            weights = getattr(prediction, "weights", None)
            if weights is not None:
                kept_weights.append(
                    weights.numpy().reshape(len(rows), -1)[episode_kept]
                )
                cold = cold_context_mask(dataset, episodes, rows)
                if cold is not None:
                    kept_cold.append(cold[episode_kept])

    if shed_count == 0:
        raise Stage4Error("every held-out hour was excluded; no primary metric exists")

    secondary = summarize(
        target=np.concatenate(kept_target),
        mean=np.concatenate(kept_mean),
        scale=np.concatenate(kept_scale),
        high_load_threshold=high_load_threshold,
        weights=np.concatenate(kept_weights) if kept_weights else None,
        cold_mask=np.concatenate(kept_cold) if kept_cold else None,
    )

    return CensoredScore(
        primary_nll=shed_total / shed_count,
        served_load_nll=all_total / all_count,
        scored_hours=shed_count,
        excluded_verified_shed_hours=excluded,
        retained_unresolved_hours=unresolved,
        total_hours=all_count,
        min_scale=min_scale,
        secondary=secondary,
    )


@dataclass
class Stage4ArmResult:
    """Outcome of one arm on one held-out event."""

    event_id: str
    arm: str
    trainable_parameters: int
    initial_loss: float
    final_loss: float
    score: CensoredScore
    context_file_sha256: str
    train_episodes: int
    event_episodes: int
    #: Best inner-validation NLL, and the step it was reached at. Stopping was
    #: chosen on this, not on the held-out event.
    inner_validation_nll: float = float("nan")
    selected_step: int = 0
    inner_validation_trace: tuple[tuple[int, float], ...] = ()


def _build_model(
    arm: str, scaffold_config: dict[str, Any], feature_dim: int, seed: int
) -> torch.nn.Module:
    """Construct one arm at the dataset's actual feature width."""
    return build_arm_model(arm, scaffold_config, feature_dim, seed)


def _inner_validation_split(
    n_episodes: int, fraction: float
) -> tuple[np.ndarray, np.ndarray]:
    """Split training episode rows into fit and inner-validation blocks.

    The split is **chronological** — the latest block validates — matching the
    stage-3 convention and the operational task. A random split would let the
    model interpolate between neighbouring days.
    """
    holdout = max(1, round(n_episodes * fraction))
    cut = n_episodes - holdout
    if cut < 1:
        raise Stage4Error("inner_validation_fraction leaves no episodes to fit on")
    return np.arange(cut), np.arange(cut, n_episodes)


def _mean_nll(
    model: torch.nn.Module,
    dataset: FoldDataset,
    episodes: EpisodeSet,
    rows: np.ndarray,
    eval_batch: int,
) -> float:
    """Mean Gaussian NLL over the given training-partition episode rows."""
    model.eval()
    total, count = 0.0, 0
    with torch.no_grad():
        for start in range(0, len(rows), eval_batch):
            batch = rows[start : start + eval_batch]
            picked = torch.tensor(
                episodes.context_indices[batch], dtype=torch.long, device=CPU
            )
            chosen = torch.tensor(
                episodes.target_rows[batch], dtype=torch.long, device=CPU
            )
            target = dataset.train_y[chosen].unsqueeze(1)
            prediction = model(
                dataset.train_x[picked],
                dataset.train_y[picked],
                dataset.train_x[chosen].unsqueeze(1),
            )
            total += float(
                gaussian_nll(target, prediction.mean, prediction.scale, reduction="sum")
            )
            count += target.numel()
    model.train()
    return total / count


@dataclass
class TrainedArm:
    """A trained arm plus the diagnostics that describe how it was selected."""

    model: torch.nn.Module
    losses: list[float]
    inner_validation_nll: float
    selected_step: int
    trace: tuple[tuple[int, float], ...]


def train_fold_arm(
    arm: str,
    scaffold_config: dict[str, Any],
    dataset: FoldDataset,
    train_episodes: EpisodeSet,
    config: Stage4Config,
) -> TrainedArm:
    """Train one arm on the fold's training partition and return the model.

    **Stopping is decided on inner validation, never on the held-out event.**
    The training episodes are split chronologically; the model is evaluated on
    the later block every ``eval_every`` steps and the parameters with the best
    inner-validation NLL are the ones returned.

    This matters more than it looks. Held-out extreme-event NLL is strongly
    non-monotone in training length — with the base feature set it *degrades* as
    the model fits the normal regime harder — so a fixed step count makes the
    reported number an artifact of that choice. Selecting on the held-out event
    would be leakage; selecting on inner validation is the leakage-free
    equivalent, and it is what makes the arms comparable to each other.

    Separated from :func:`run_fold_arm` so that prediction capture can reuse the
    exact training path rather than reimplementing it — a second copy of this
    loop would be free to drift from the one that produced the results.
    """
    model = _build_model(arm, scaffold_config, dataset.train.x.shape[1], config.seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    generator = seeded_generator(config.seed)

    fit_rows, val_rows = _inner_validation_split(
        len(train_episodes), config.inner_validation_fraction
    )
    n_fit = len(fit_rows)

    best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    best_val = float("inf")
    best_step = 0
    trace: list[tuple[int, float]] = []

    model.train()
    losses: list[float] = []
    for step in range(1, config.steps + 1):
        rows = fit_rows[
            torch.randint(0, n_fit, (config.batch_size,), generator=generator).numpy()
        ]
        picked = torch.tensor(
            train_episodes.context_indices[rows], dtype=torch.long, device=CPU
        )
        chosen = torch.tensor(
            train_episodes.target_rows[rows], dtype=torch.long, device=CPU
        )
        prediction = model(
            dataset.train_x[picked],
            dataset.train_y[picked],
            dataset.train_x[chosen].unsqueeze(1),
        )
        loss = gaussian_nll(
            dataset.train_y[chosen].unsqueeze(1), prediction.mean, prediction.scale
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))

        if step % config.eval_every == 0 or step == config.steps:
            val = _mean_nll(model, dataset, train_episodes, val_rows, config.eval_batch)
            trace.append((step, val))
            if val < best_val:
                best_val = val
                best_step = step
                best_state = {
                    k: v.detach().clone() for k, v in model.state_dict().items()
                }

    model.load_state_dict(best_state)
    return TrainedArm(
        model=model,
        losses=losses,
        inner_validation_nll=best_val,
        selected_step=best_step,
        trace=tuple(trace),
    )


def run_fold_arm(
    arm: str,
    scaffold_config: dict[str, Any],
    dataset: FoldDataset,
    train_episodes: EpisodeSet,
    event_episodes: EpisodeSet,
    censoring: CensoringIndex,
    config: Stage4Config,
) -> Stage4ArmResult:
    """Train one arm and score the held-out event under D-010."""
    trained = train_fold_arm(arm, scaffold_config, dataset, train_episodes, config)
    score = score_held_out_event(
        trained.model, dataset, event_episodes, censoring, config
    )

    return Stage4ArmResult(
        event_id=dataset.partition.fold.event_id,
        arm=arm,
        trainable_parameters=sum(
            p.numel() for p in trained.model.parameters() if p.requires_grad
        ),
        initial_loss=trained.losses[0],
        final_loss=trained.losses[-1],
        score=score,
        context_file_sha256=event_episodes.context_file.sha256,
        train_episodes=len(train_episodes),
        event_episodes=len(event_episodes),
        inner_validation_nll=trained.inner_validation_nll,
        selected_step=trained.selected_step,
        inner_validation_trace=trained.trace,
    )


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_run_manifest(
    path: str | Path,
    result: Stage4ArmResult,
    config: Stage4Config,
    eligible: EligibleEvents,
    censoring: CensoringIndex,
    input_hashes: dict[str, str],
    config_sha256: str,
    train_context_sha256: str,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Emit the stage-4 manifest with every field the run plan requires."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    score = result.score
    payload = {
        "run_id": f"stage4_{result.event_id}_{result.arm}_seed{config.seed}",
        "stage": 4,
        "result_label": RESULT_LABEL,
        "authorization": "D-011 (stage 4 exploratory only; stages 5 and 6 blocked)",
        "event_id": result.event_id,
        "arm": result.arm,
        "seed": config.seed,
        "context_size": config.context_size,
        "config_sha256": config_sha256,
        "input_artifact_sha256": input_hashes,
        "context_index_file_sha256": {
            "train": train_context_sha256,
            "held_out_event": result.context_file_sha256,
        },
        "trainable_parameter_count": result.trainable_parameters,
        "derived_fold_count": len(eligible.event_ids),
        "fold_count_derived_not_literal": True,
        "censoring_treatment_applied": CENSORING_TREATMENT,
        "censoring_counts_for_event": censoring.counts_for_event(result.event_id),
        "excluded_verified_shed_hours": score.excluded_verified_shed_hours,
        "retained_unresolved_hours": score.retained_unresolved_hours,
        "primary_nll_latent_demand_normalized_units": score.primary_nll,
        "primary_nll_scored_hours": score.scored_hours,
        "served_load_nll_all_hours_normalized_units": score.served_load_nll,
        "served_load_nll_estimand": "served load, not latent demand",
        "total_held_out_hours": score.total_hours,
        "min_predicted_scale": score.min_scale,
        # Freeze §7 secondary metrics. Reported for interpretation; they do not
        # adjudicate the comparison. Definitions pre-registered in
        # docs/track_a/ANALYSIS_PLAN_v1.md.
        "secondary_metrics": (
            score.secondary.as_dict() if score.secondary is not None else None
        ),
        "train_episodes": result.train_episodes,
        "held_out_episodes": result.event_episodes,
        "initial_training_loss": result.initial_loss,
        "final_training_loss": result.final_loss,
        "inner_validation_nll": result.inner_validation_nll,
        "selected_step": result.selected_step,
        "stopping_selected_on": (
            "inner validation drawn from the fold training partition; "
            "never on the held-out event"
        ),
        "inner_validation_trace": [list(p) for p in result.inner_validation_trace],
        "normalization_fitted_on": "fold training partition only",
        "buffer_days_excluded_from_training_and_retrieval": BUFFER_DAYS,
        "disclosure": (
            "EXPLORATORY. Primary metric excludes verified_shed hours "
            f"({score.excluded_verified_shed_hours} for this event). unresolved "
            f"hours ({score.retained_unresolved_hours}) are retained and flagged; "
            "their censoring status is unknown and is not resolved in either "
            "direction. Served-load diagnostic reports a different estimand "
            "(served load, not latent demand)."
        ),
    }
    if extra:
        payload.update(extra)
        payload["run_id"] = (
            f"stage4_{result.event_id}_{result.arm}"
            f"_{extra.get('feature_set', 'base')}"
            f"_{extra.get('context_condition', 'nearest')}_seed{config.seed}"
        )
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
