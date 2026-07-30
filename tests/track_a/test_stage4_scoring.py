"""Tests for the D-010 censoring arithmetic in stage-4 scoring.

`stage4.score_held_out_event` applies the adopted censoring ruling: it excludes
``verified_shed`` hours from the primary latent-demand NLL, retains and counts
``unresolved`` hours, and reports an all-hours served-load NLL. None of that was
covered by any test.

These tests use a **stub model with constant mean and scale**, so every NLL is
analytically known and the exclusion arithmetic can be checked exactly rather
than compared against the code's own output. No real artifact is read and no
trained model is involved.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from ercot_forecasting.track_a.censoring import (
    UNRESOLVED,
    VERIFIED_SHED,
    CensoringIndex,
)
from ercot_forecasting.track_a.partition import HORIZON
from ercot_forecasting.track_a.stage3 import ContextIndexFile, EpisodeSet
from ercot_forecasting.track_a.stage4 import Stage4Config, score_held_out_event

#: Constant prediction the stub emits, so the NLL per hour is closed-form.
STUB_MEAN = 0.0
STUB_SCALE = 1.0

N_EVENT_DAYS = 3
N_TRAIN_DAYS = 8
CONTEXT_SIZE = 2


@dataclass
class _Prediction:
    mean: torch.Tensor
    scale: torch.Tensor


class _StubModel(torch.nn.Module):
    """Emits a constant Gaussian, ignoring its inputs."""

    def eval(self):
        return self

    def forward(self, context_x, context_y, target_x) -> _Prediction:
        shape = (target_x.shape[0], target_x.shape[1], HORIZON)
        return _Prediction(
            mean=torch.full(shape, STUB_MEAN, dtype=torch.float32),
            scale=torch.full(shape, STUB_SCALE, dtype=torch.float32),
        )


@dataclass
class _FoldDatasetStub:
    """Minimal stand-in exposing only what the scorer reads."""

    train_x: torch.Tensor
    train_y: torch.Tensor
    event_x: torch.Tensor
    event_y: torch.Tensor
    event_hours: tuple[pd.DatetimeIndex, ...]
    partition: object = None


def _hand_nll(y: float) -> float:
    """−log N(y | 0, 1) written longhand."""
    return 0.5 * math.log(2.0 * math.pi) + 0.5 * y * y


@pytest.fixture
def event_hours() -> tuple[pd.DatetimeIndex, ...]:
    """Three consecutive 24-hour UTC days."""
    return tuple(
        pd.date_range(f"2021-02-1{d + 2} 00:00", periods=HORIZON, freq="h", tz="UTC")
        for d in range(N_EVENT_DAYS)
    )


@pytest.fixture
def dataset(event_hours) -> _FoldDatasetStub:
    """Held-out targets are all 1.0, so every hour's NLL is identical."""
    return _FoldDatasetStub(
        train_x=torch.zeros((N_TRAIN_DAYS, 4), dtype=torch.float32),
        train_y=torch.zeros((N_TRAIN_DAYS, HORIZON), dtype=torch.float32),
        event_x=torch.zeros((N_EVENT_DAYS, 4), dtype=torch.float32),
        event_y=torch.ones((N_EVENT_DAYS, HORIZON), dtype=torch.float32),
        event_hours=event_hours,
    )


@pytest.fixture
def episodes(event_hours) -> EpisodeSet:
    return EpisodeSet(
        days=tuple(h.min().date() for h in event_hours),
        target_rows=np.arange(N_EVENT_DAYS),
        context_indices=np.zeros((N_EVENT_DAYS, CONTEXT_SIZE), dtype=np.int64),
        context_file=ContextIndexFile(
            path=Path("unused.csv"),
            sha256="0" * 64,
            n_episodes=N_EVENT_DAYS,
            context_size=CONTEXT_SIZE,
            indices=np.zeros((N_EVENT_DAYS, CONTEXT_SIZE), dtype=np.int64),
            target_positions=np.arange(N_EVENT_DAYS),
        ),
    )


def _censoring(shed: pd.DatetimeIndex, unresolved: pd.DatetimeIndex) -> CensoringIndex:
    frame = pd.DataFrame(
        {
            "ts_utc": list(shed) + list(unresolved),
            "event_id": "E_TEST",
            "censor_status": [VERIFIED_SHED] * len(shed)
            + [UNRESOLVED] * len(unresolved),
        }
    )
    return CensoringIndex(
        frame=frame,
        shed_hours=frozenset(shed),
        unresolved_hours=frozenset(unresolved),
    )


def _config() -> Stage4Config:
    return Stage4Config(seed=1, context_size=CONTEXT_SIZE, steps=1, eval_batch=2)


def test_scored_plus_excluded_equals_total(dataset, episodes, event_hours) -> None:
    """The exclusion partitions the held-out hours; nothing is lost or double-counted."""
    shed = event_hours[0][:5]
    censoring = _censoring(shed, event_hours[1])

    score = score_held_out_event(_StubModel(), dataset, episodes, censoring, _config())

    assert score.total_hours == N_EVENT_DAYS * HORIZON
    assert score.excluded_verified_shed_hours == len(shed)
    assert score.scored_hours + score.excluded_verified_shed_hours == score.total_hours


def test_primary_excludes_shed_and_served_load_includes_it(
    dataset, episodes, event_hours
) -> None:
    """Both metrics equal the closed-form value; only their denominators differ.

    Every target is 1.0 and the stub predicts N(0, 1), so each hour contributes
    exactly ``_hand_nll(1.0)``. The two means must therefore be *equal* here —
    which is the point: it isolates the counting from the arithmetic.
    """
    censoring = _censoring(event_hours[0][:7], event_hours[1])
    expected = _hand_nll(1.0)

    score = score_held_out_event(_StubModel(), dataset, episodes, censoring, _config())

    assert score.primary_nll == pytest.approx(expected, rel=1e-6)
    assert score.served_load_nll == pytest.approx(expected, rel=1e-6)


def test_excluding_worse_hours_lowers_the_primary_metric(
    dataset, episodes, event_hours
) -> None:
    """With a bad day excluded, the primary metric must beat the all-hours one.

    Day 0's targets are made extreme, so its hours carry a much higher NLL.
    Marking exactly those hours `verified_shed` must pull the primary metric
    below the served-load diagnostic. This is the check that would catch an
    inverted mask.
    """
    dataset.event_y[0, :] = 50.0
    censoring = _censoring(event_hours[0], event_hours[1])

    score = score_held_out_event(_StubModel(), dataset, episodes, censoring, _config())

    assert score.excluded_verified_shed_hours == HORIZON
    assert score.primary_nll == pytest.approx(_hand_nll(1.0), rel=1e-6)
    assert score.primary_nll < score.served_load_nll


def test_unresolved_hours_are_counted_but_not_excluded(
    dataset, episodes, event_hours
) -> None:
    """`unresolved` hours are retained in the primary metric and reported (D-010 §3.2)."""
    censoring = _censoring(event_hours[0][:4], event_hours[1])

    score = score_held_out_event(_StubModel(), dataset, episodes, censoring, _config())

    assert score.retained_unresolved_hours == HORIZON
    # Retained, so they are inside the scored set rather than removed from it.
    assert score.scored_hours == score.total_hours - 4


def test_hours_outside_the_censoring_record_are_scored(dataset, episodes) -> None:
    """A day with no censoring row at all is scored, not silently dropped."""
    empty = pd.DatetimeIndex([], dtype="datetime64[ns, UTC]")
    score = score_held_out_event(
        _StubModel(), dataset, episodes, _censoring(empty, empty), _config()
    )

    assert score.excluded_verified_shed_hours == 0
    assert score.retained_unresolved_hours == 0
    assert score.scored_hours == score.total_hours == N_EVENT_DAYS * HORIZON


def test_day_ordering_aligns_with_the_censoring_mask(
    dataset, episodes, event_hours
) -> None:
    """The mask must line up with the episode whose hours it describes.

    Day 2 is made extreme and day 2's hours are marked shed. If the scorer
    misaligned episodes and timestamps, the extreme day would survive into the
    primary metric and it would not equal the clean closed-form value.
    """
    dataset.event_y[2, :] = 50.0
    censoring = _censoring(event_hours[2], pd.DatetimeIndex([], tz="UTC"))

    score = score_held_out_event(_StubModel(), dataset, episodes, censoring, _config())

    assert score.excluded_verified_shed_hours == HORIZON
    assert score.primary_nll == pytest.approx(_hand_nll(1.0), rel=1e-6)


def test_all_hours_excluded_raises_rather_than_reporting_an_empty_mean(
    dataset, episodes, event_hours
) -> None:
    """No primary metric exists if every hour is censored; that must fail loudly."""
    every_hour = pd.DatetimeIndex(np.concatenate([np.asarray(h) for h in event_hours]))
    censoring = _censoring(every_hour, pd.DatetimeIndex([], tz="UTC"))

    with pytest.raises(Exception, match="every held-out hour was excluded"):
        score_held_out_event(_StubModel(), dataset, episodes, censoring, _config())
