"""Validation tests for the imported controlling event inventory.

These run against the real, hash-verified artifact adopted by D-006. They read
event-level metadata only. They perform no held-out-event prediction and no
performance inspection of any kind.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ercot_forecasting.track_a.event_inventory import (
    REQUIRED_COLUMNS,
    InventoryValidationError,
    event_count,
    load_event_inventory,
    localize_inventory,
    timezone_is_declared,
    validate_event_inventory,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY = REPO_ROOT / "data" / "shared" / "event_inventory_headline.csv"

pytestmark = pytest.mark.skipif(
    not INVENTORY.is_file(),
    reason="controlling event inventory has not been imported",
)


def test_inventory_schema_matches_required_columns():
    frame = load_event_inventory(INVENTORY)
    assert tuple(frame.columns) == REQUIRED_COLUMNS


def test_inventory_passes_validation():
    report = validate_event_inventory(INVENTORY)
    assert report.duplicate_onsets == 0
    assert report.non_positive_durations == 0
    assert report.onsets_monotonic


def test_event_count_is_derived_not_hard_coded():
    """D-006 and freeze 10.1: the count must come from the artifact.

    This test deliberately asserts a *relationship* rather than a literal: the
    derived count must equal the number of data rows actually present. No event
    or fold count is named anywhere in this file.
    """
    frame = load_event_inventory(INVENTORY)
    with open(INVENTORY, encoding="utf-8") as handle:
        raw_rows = sum(1 for _ in handle) - 1  # minus the header line
    assert event_count(frame) == raw_rows
    assert event_count(frame) > 0


def test_inventory_declares_no_timezone():
    """The artifact carries no timezone designator (ARTIFACT_INVENTORY 8.2).

    Recorded as a test so that if a future artifact revision adds one, this
    fails loudly rather than silently changing the alignment semantics.
    """
    frame = load_event_inventory(INVENTORY)
    assert timezone_is_declared(frame) is False


def test_fixed_utc_offsets_are_rejected():
    """D-007: fixed offsets are prohibited; DST needs a timezone database.

    Bare ``UTC`` is deliberately NOT in this list: it is a real IANA zone and is
    the convention the controlling builder applies to these timestamps. Only
    offset-shaped arguments are rejected.
    """
    frame = load_event_inventory(INVENTORY)
    for bad in ("UTC-06:00", "GMT+6", "utc-6", ""):
        with pytest.raises(InventoryValidationError):
            localize_inventory(frame, bad)


def test_bare_utc_is_accepted_as_an_iana_zone():
    """The UTC convention must not be blocked by the fixed-offset guard.

    `event_eligibility` localizes the naive inventory to UTC, following the
    controlling builder. If this module rejected "UTC", the two would assert
    contradictory positions on the same timestamps.
    """
    frame = load_event_inventory(INVENTORY)
    localized = localize_inventory(frame, "UTC")
    assert str(localized["onset"].dt.tz) == "UTC"
    assert (localized["onset"].dt.tz_localize(None) == frame["onset"]).all()


def test_explicit_iana_zone_localizes_to_utc():
    """An explicit IANA zone converts cleanly; nothing is inferred by default."""
    frame = load_event_inventory(INVENTORY)
    localized = localize_inventory(frame, "America/Chicago")
    assert str(localized["onset"].dt.tz) == "UTC"
    # The naive frame must be left untouched.
    assert timezone_is_declared(frame) is False


def test_events_do_not_overlap():
    """Distinct events must not overlap; overlapping windows would make the
    leave-one-event-out partition ill-defined."""
    frame = load_event_inventory(INVENTORY).sort_values("onset").reset_index(drop=True)
    previous_recovery = None
    for _, row in frame.iterrows():
        if previous_recovery is not None:
            assert row["onset"] > previous_recovery, (
                f"event starting {row['onset']} overlaps the previous recovery "
                f"{previous_recovery}"
            )
        previous_recovery = row["recovery"]


def test_declared_hours_use_inclusive_endpoint_counting():
    """The `hours` column counts both endpoint hours.

    Verified against the artifact: every event satisfies
    ``hours == (recovery - onset) / 1h + 1``. For example the first event spans
    1996-01-31 22:00 to 1996-02-05 21:00, an elapsed 119 hours, and declares
    120 -- i.e. the onset hour and the recovery hour are both counted.

    This convention is recorded as a test because it determines how many hourly
    observations an event window contains, which in turn affects the +/-7-day
    buffer arithmetic and any event-hour exclusion.
    """
    frame = load_event_inventory(INVENTORY)
    elapsed = (frame["recovery"] - frame["onset"]) / pd.Timedelta(hours=1)
    mismatches = frame.loc[(elapsed + 1 - frame["hours"]).abs() > 1e-9]
    assert mismatches.empty, (
        f"{len(mismatches)} events deviate from inclusive-endpoint hour counting"
    )
