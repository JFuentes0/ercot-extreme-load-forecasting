"""Stage-4 leave-one-event-out leakage tests (freeze §3, D-011).

These assert the structural protections that make a held-out-event result
meaningful: the held-out event and its ±7-day buffer are absent from training
**and** from context retrieval, including through the lag features, and both
arms consume byte-identical context-index files.

The tests build partitions and read timestamps. They train no model and inspect
no event-period model performance.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ercot_forecasting.track_a.event_eligibility import derive_eligible_events
from ercot_forecasting.track_a.features import LAG_HOURS, build_episode_arrays
from ercot_forecasting.track_a.load_data import load_harmonized
from ercot_forecasting.track_a.partition import (
    BUFFER_DAYS,
    build_loeo_folds,
    build_target_days,
    issuance_cutoff_utc,
)
from ercot_forecasting.track_a.stage4 import (
    Stage4Config,
    build_fold_dataset,
    build_fold_episodes,
    episode_lag_start,
    partition_fold_days,
    read_context_indices,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LOAD = REPO_ROOT / "data" / "frozen" / "track_a" / "ercot_hourly_load_harmonized.csv"
INVENTORY = REPO_ROOT / "data" / "shared" / "event_inventory_headline.csv"

pytestmark = pytest.mark.skipif(
    not (LOAD.is_file() and INVENTORY.is_file()),
    reason="Track A artifacts not imported",
)

#: A small context set keeps these tests fast; identity, not size, is the claim.
TEST_CONTEXT_SIZE = 8


@pytest.fixture(scope="module")
def artifacts():
    load = load_harmonized(LOAD, usable_only=True)
    eligible = derive_eligible_events(INVENTORY, LOAD)
    return load, eligible, build_target_days(load)


@pytest.fixture(scope="module")
def folds(artifacts):
    _load, eligible, _index = artifacts
    return build_loeo_folds(eligible)


@pytest.fixture(scope="module")
def partitions(artifacts, folds):
    """Every fold's partition, built once — the split is deterministic."""
    load, _eligible, index = artifacts
    return {fold.event_id: partition_fold_days(load, fold, index) for fold in folds}


@pytest.fixture(scope="module")
def sample_episodes(artifacts, folds, partitions, tmp_path_factory):
    """One fold carried through to persisted context indices.

    Built once: the episode construction reads the whole load frame, and the
    identity claims below do not depend on which fold is used.
    """
    load, _eligible, index = artifacts
    fold = folds[0]
    config = Stage4Config(seed=20260729, context_size=TEST_CONTEXT_SIZE)
    dataset = build_fold_dataset(load, partitions[fold.event_id], index)
    train_set, event_set = build_fold_episodes(
        dataset, config, tmp_path_factory.mktemp("stage4_context")
    )
    return fold, dataset, train_set, event_set


def test_fold_count_is_derived_from_the_inventory(artifacts, folds) -> None:
    """One fold per load-eligible event, derived — never a literal (D-006)."""
    _load, eligible, _index = artifacts
    assert len(folds) == len(eligible.event_ids)


def test_no_training_day_falls_inside_the_buffered_window(
    artifacts, folds, partitions
) -> None:
    """The held-out event and its buffer are absent from training (freeze §3)."""
    _load, _eligible, index = artifacts
    for fold in folds:
        for day in partitions[fold.event_id].train_days:
            hours = index.hours[day]
            assert not (
                (hours.min() <= fold.buffer_hi) and (hours.max() >= fold.buffer_lo)
            ), f"{fold.event_id}: training day {day} intersects the buffer"


def test_training_lag_windows_stay_outside_the_buffer(
    artifacts, folds, partitions
) -> None:
    """A training day's own lag window may not reach into the buffer.

    A day just past the buffer edge would otherwise carry held-out hours into
    training through its features, which the buffer exists to prevent.

    The expected earliest lag hour is recovered **from the load axis itself** —
    the same `searchsorted` walk `build_episode_arrays` performs — rather than
    from any constant the implementation defines. An earlier revision of this
    test hard-coded a 25-hour span, which was the implementation's own (wrong)
    constant, so the assertion restated the bug instead of catching it. The lag
    actually reaches ~39 hours back, because the issuance cutoff sits 15 hours
    before the target day begins.
    """
    load, _eligible, index = artifacts
    stamps = (
        load["ts_utc"]
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
        .to_numpy("datetime64[ns]")
    )

    def observed_lag_start(day) -> pd.Timestamp:
        """Earliest hour `build_episode_arrays` would place in this day's lag."""
        cutoff = issuance_cutoff_utc(day).tz_convert("UTC").tz_localize(None)
        limit = np.datetime64(cutoff) - np.timedelta64(1, "h")
        end = int(np.searchsorted(stamps, limit, side="right"))
        return pd.Timestamp(stamps[end - LAG_HOURS]).tz_localize("UTC")

    for fold in folds:
        for day in partitions[fold.event_id].train_days:
            lag_start = observed_lag_start(day)
            assert not (
                (lag_start <= fold.buffer_hi)
                and (index.hours[day].max() >= fold.buffer_lo)
            ), (
                f"{fold.event_id}: lag window of {day} starts {lag_start} and "
                f"reaches into buffer [{fold.buffer_lo}, {fold.buffer_hi}]"
            )


def test_episode_lag_start_matches_the_real_lag_window(artifacts) -> None:
    """`episode_lag_start` agrees with what `build_episode_arrays` actually reads.

    This is the guard on the guard: if the two ever diverge, the partition rule
    is filtering against a window the feature builder does not use.
    """
    load, _eligible, index = artifacts
    stamps = (
        load["ts_utc"]
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
        .to_numpy("datetime64[ns]")
    )

    # Sample across the record, including both DST regimes.
    for day in index.days[::373]:
        cutoff = issuance_cutoff_utc(day).tz_convert("UTC").tz_localize(None)
        limit = np.datetime64(cutoff) - np.timedelta64(1, "h")
        end = int(np.searchsorted(stamps, limit, side="right"))
        if end < LAG_HOURS:
            continue
        observed = pd.Timestamp(stamps[end - LAG_HOURS]).tz_localize("UTC")
        assert episode_lag_start(day) == observed, day


def test_every_held_out_day_overlaps_its_event(artifacts, folds, partitions) -> None:
    """Held-out days are the event's own days, not the buffer's."""
    _load, _eligible, index = artifacts
    for fold in folds:
        for day in partitions[fold.event_id].event_days:
            hours = index.hours[day]
            assert (hours.min() <= fold.recovery) and (hours.max() >= fold.onset)


def test_buffer_days_are_excluded_from_both_sides(folds, partitions) -> None:
    """Days inside the buffer but outside the event enter neither set."""
    for fold in folds:
        partition = partitions[fold.event_id]
        assert set(partition.excluded_days).isdisjoint(partition.train_days)
        assert set(partition.excluded_days).isdisjoint(partition.event_days)
        assert partition.excluded_days, (
            f"{fold.event_id}: a ±{BUFFER_DAYS}-day buffer excluded no day at all"
        )


def test_retrieval_never_draws_from_the_held_out_window(sample_episodes) -> None:
    """Context days come only from the fold's admissible training pool."""
    fold, dataset, _train_set, event_set = sample_episodes
    pool = dataset.train.days
    for row in event_set.context_indices:
        for position in row:
            day = pool[int(position)]
            assert not (fold.buffer_lo.date() <= day <= fold.buffer_hi.date())


def test_both_arms_read_the_same_context_bytes(sample_episodes) -> None:
    """The persisted file, re-read, reproduces the selection both arms consume."""
    _fold, _dataset, _train_set, event_set = sample_episodes
    reread = read_context_indices(event_set.context_file.path)
    assert (reread == event_set.context_indices).all()
    assert event_set.context_indices.shape[1] == TEST_CONTEXT_SIZE


def test_normalization_is_fitted_on_training_days_only(
    artifacts, folds, partitions
) -> None:
    """The normalizer is invariant to the held-out event's target values.

    An earlier version of this test asserted
    ``normalizer.y_mean == dataset.train.y.mean()`` — which is the literal body
    of ``Normalizer.fit`` applied to the same array, so it was ``x == x`` and
    could not fail. It restated the implementation instead of checking the
    property its own docstring claimed.

    This version perturbs the held-out episodes by a large constant and asserts
    the normalizer is unchanged. That is the actual claim: held-out targets do
    not inform the normalization.
    """
    load, _eligible, index = artifacts
    fold = folds[0]
    partition = partitions[fold.event_id]

    baseline = build_fold_dataset(load, partition, index)

    perturbed_episodes = build_episode_arrays(load, index)
    for day in partition.event_days:
        row = perturbed_episodes.days.index(day)
        perturbed_episodes.y[row] += 1.0e6

    perturbed = build_fold_dataset(load, partition, index, perturbed_episodes)

    assert perturbed.normalizer.y_mean == pytest.approx(baseline.normalizer.y_mean)
    assert perturbed.normalizer.y_std == pytest.approx(baseline.normalizer.y_std)
    # ...and the perturbation really did reach the held-out episodes, so the
    # invariance above is meaningful rather than a no-op.
    assert perturbed.event.y.mean() > baseline.event.y.mean() + 1.0e5
