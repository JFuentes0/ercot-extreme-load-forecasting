"""Workstream-4 partition and issuance-safeguard tests.

These assert the structural leakage protections the freeze requires: the
issuance cutoff, the ±7-day buffer, leave-one-event-out exclusion from training
**and** retrieval, and the stage-3 requirement that no event-period hour appears.

They read timestamps and event windows only. No model is built, no prediction is
made, and no event-period model performance is computed or inspected.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from ercot_forecasting.track_a.event_eligibility import derive_eligible_events
from ercot_forecasting.track_a.load_data import (
    CALENDAR_ZONE,
    TARGET_COLUMN,
    load_harmonized,
    local_calendar_day,
)
from ercot_forecasting.track_a.partition import (
    BUFFER_DAYS,
    HORIZON,
    ISSUANCE_LOCAL_HOUR,
    build_loeo_folds,
    build_target_days,
    event_hour_mask,
    fold_training_mask,
    issuance_cutoff_utc,
    issuance_safe_candidates,
    stage3_target_days,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LOAD = REPO_ROOT / "data" / "frozen" / "track_a" / "ercot_hourly_load_harmonized.csv"
INVENTORY = REPO_ROOT / "data" / "shared" / "event_inventory_headline.csv"

pytestmark = pytest.mark.skipif(
    not (LOAD.is_file() and INVENTORY.is_file()),
    reason="governing artifacts have not been imported",
)


@pytest.fixture(scope="module")
def load():
    return load_harmonized(LOAD)


@pytest.fixture(scope="module")
def eligible():
    return derive_eligible_events(INVENTORY, LOAD)


@pytest.fixture(scope="module")
def folds(eligible):
    return build_loeo_folds(eligible)


@pytest.fixture(scope="module")
def targets(load):
    return build_target_days(load)


# --- issuance cutoff -------------------------------------------------------


def test_issuance_cutoff_is_0900_local_on_d_minus_1():
    """Freeze §5 / D-007: 09:00 America/Chicago on D-1."""
    target = date(2021, 2, 16)
    cutoff = issuance_cutoff_utc(target)
    local = cutoff.tz_convert(ZoneInfo(CALENDAR_ZONE))
    assert local.hour == ISSUANCE_LOCAL_HOUR
    assert local.minute == 0
    assert local.date() == target - timedelta(days=1)


def test_issuance_cutoff_tracks_dst_not_a_fixed_offset():
    """The UTC hour of the cutoff must differ between CST and CDT.

    A fixed offset would give the same UTC hour year-round. D-007 requires the
    timezone database to move it.
    """
    winter = issuance_cutoff_utc(date(2021, 1, 15))
    summer = issuance_cutoff_utc(date(2021, 7, 15))
    assert winter.hour != summer.hour
    for cutoff in (winter, summer):
        local = cutoff.tz_convert(ZoneInfo(CALENDAR_ZONE))
        assert local.hour == ISSUANCE_LOCAL_HOUR


def test_every_target_hour_falls_after_its_issuance_cutoff(targets):
    """A target day's own hours must never precede its cutoff.

    If they did, part of the target day would be observable at issuance.
    """
    for day in targets.days[:200]:
        cutoff = issuance_cutoff_utc(day)
        assert targets.hours[day].min() > cutoff


# --- target-day construction ----------------------------------------------


def test_target_days_are_exactly_the_horizon_long(targets):
    """Freeze §6: a target vector is exactly 24 hours."""
    assert len(targets) > 0
    for day in targets.days[:500]:
        assert len(targets.hours[day]) == HORIZON


def test_dst_days_are_excluded_from_target_construction(targets):
    """23- and 25-hour local days cannot form a 24-hour vector."""
    assert len(targets.excluded_dst_days) > 0
    assert set(targets.excluded_dst_days).isdisjoint(set(targets.days))


def test_days_with_missing_target_values_are_excluded(targets, load):
    """No usable target day may contain a null target value.

    Asserted as a property of the *result*, not of the `excluded_incomplete`
    list. In the adopted artifact the single null falls on 2016-11-06, a 25-hour
    fall-back day, so the DST check excludes it first and the incomplete list is
    empty. Asserting that list alone would pass vacuously; this asserts the
    thing that actually matters.
    """
    assert set(targets.excluded_incomplete_days).isdisjoint(set(targets.days))

    null_days = set(local_calendar_day(load.loc[load[TARGET_COLUMN].isna(), "ts_utc"]))
    assert null_days.isdisjoint(set(targets.days)), (
        f"a day containing a null target survived as usable: {null_days}"
    )


def test_null_target_exclusion_branch_actually_works():
    """Exercise the null-exclusion path, which real data never triggers.

    Because the only null coincides with a DST day, the incomplete-day branch is
    dead code against the adopted artifact. A synthetic full 24-hour day with one
    null proves the branch works, so it cannot rot unnoticed.
    """
    hours = pd.date_range("2015-01-15 06:00", periods=HORIZON, freq="h", tz="UTC")
    frame = pd.DataFrame({"ts_utc": hours, TARGET_COLUMN: [1000.0] * HORIZON})
    clean = build_target_days(frame)
    assert len(clean) == 1, "a complete synthetic day should be usable"

    frame.loc[5, TARGET_COLUMN] = None
    holed = build_target_days(frame)
    assert len(holed) == 0
    assert len(holed.excluded_incomplete_days) == 1
    assert not holed.excluded_dst_days


# --- retrieval / issuance safety -------------------------------------------


def test_issuance_safe_candidates_all_precede_the_cutoff(targets):
    """Freeze §3: all context days must precede the target issuance time."""
    chosen = targets.days[len(targets.days) // 2]
    cutoff = issuance_cutoff_utc(chosen)
    window = targets.days[: targets.days.index(chosen)][-400:]
    safe = issuance_safe_candidates(chosen, tuple(window), targets)
    assert len(safe) > 0
    for day in safe:
        assert targets.hours[day].max() < cutoff
    assert chosen not in safe


def test_the_target_day_is_never_its_own_context(targets):
    chosen = targets.days[len(targets.days) // 2]
    safe = issuance_safe_candidates(chosen, targets.days, targets)
    assert chosen not in safe


# --- LOEO folds and buffers ------------------------------------------------


def test_fold_count_equals_eligible_event_count(eligible, folds):
    """Derived, never hard-coded (D-006, freeze §10.1)."""
    assert len(folds) == eligible.fold_count
    assert len(folds) > 0


def test_buffer_is_seven_days_either_side(eligible, folds):
    """Freeze §3: ±7-day buffer around the held-out event."""
    pad = pd.Timedelta(days=BUFFER_DAYS)
    for fold, (_, event) in zip(folds, eligible.table.iterrows(), strict=True):
        assert fold.buffer_lo == event["onset"] - pad
        assert fold.buffer_hi == event["recovery"] + pad


def test_fold_excludes_its_event_and_buffer_from_training_and_retrieval(load, folds):
    """The same mask governs training and retrieval, so neither can leak."""
    stamps = load["ts_utc"]
    for fold in folds:
        admissible = fold_training_mask(stamps, fold)
        inside = (stamps >= fold.buffer_lo) & (stamps <= fold.buffer_hi)
        assert not admissible[inside].any()
        assert inside.sum() > 0


def test_held_out_event_hours_are_never_admissible_in_its_own_fold(load, folds):
    stamps = load["ts_utc"]
    for fold in folds:
        admissible = fold_training_mask(stamps, fold)
        event_hours = (stamps >= fold.onset) & (stamps <= fold.recovery)
        assert not admissible[event_hours].any()


def test_other_events_remain_available_in_a_given_fold(load, folds, eligible):
    """LOEO holds out one event, not all of them."""
    if len(folds) < 2:
        pytest.skip("needs at least two folds")
    stamps = load["ts_utc"]
    fold = folds[0]
    admissible = fold_training_mask(stamps, fold)
    other = eligible.table.iloc[1]
    other_hours = (stamps >= other["onset"]) & (stamps <= other["recovery"])
    assert admissible[other_hours].any()


# --- stage 3: no event-period hour -----------------------------------------


def test_stage3_excludes_every_event_period_hour(load, eligible):
    """D-008 and freeze §11.1: asserted by test, never by inspection."""
    usable, rejected = stage3_target_days(load, eligible)
    event_hours = set(
        load.loc[event_hour_mask(load["ts_utc"], eligible, buffer_days=0), "ts_utc"]
    )
    assert len(event_hours) > 0
    for day in usable.days:
        assert event_hours.isdisjoint(set(usable.hours[day])), (
            f"stage-3 day {day} contains an event-period hour"
        )
    assert len(rejected) > 0


def test_stage3_leaves_a_usable_majority_of_days(load, eligible):
    """Excluding event hours must not gut the normal-period sample."""
    usable, rejected = stage3_target_days(load, eligible)
    assert len(usable) > len(rejected)
    assert len(usable) > 0
