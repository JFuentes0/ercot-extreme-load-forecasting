"""Eligibility, fold-count derivation, and exploratory-event verification.

Every expected value here is derived from the **governing artifacts** — the
D-006 inventory and the D-009 load artifact — never from a downstream product.
An earlier version asserted the fold count against
``v7_demand_censored_v3.csv``'s distinct ``event_id`` count while the code under
test also read that same column, so the assertion compared the artifact with
itself and could not fail. The censoring artifact now appears only in one
clearly-labelled independent cross-check.

These tests read event-level metadata and timestamps. They perform no
held-out-event prediction and inspect no model performance.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ercot_forecasting.track_a.event_eligibility import (
    EligibilityError,
    assign_event_ids,
    derive_eligible_events,
    derive_load_span,
    event_hour_index,
)
from ercot_forecasting.track_a.event_inventory import load_event_inventory

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY = REPO_ROOT / "data" / "shared" / "event_inventory_headline.csv"
LOAD = REPO_ROOT / "data" / "frozen" / "track_a" / "ercot_hourly_load_harmonized.csv"
CENSORING = REPO_ROOT / "data" / "frozen" / "track_a" / "v7_demand_censored_v3.csv"

#: Events the committed contract names for the stage-4 exploratory runs.
#: Identifiers, not counts; they assert nothing about inventory size.
EXPLORATORY_EVENT_IDS = ("E08_20110202", "E14_20210212", "E21_20260125")

pytestmark = pytest.mark.skipif(
    not (INVENTORY.is_file() and LOAD.is_file()),
    reason="governing artifacts have not been imported",
)


@pytest.fixture(scope="module")
def eligible():
    return derive_eligible_events(INVENTORY, LOAD)


def test_load_span_is_usable_and_unique():
    """The controlling builder asserts a unique UTC axis before deriving lo/hi."""
    span = derive_load_span(LOAD)
    assert span.axis_is_unique
    assert span.usable_rows > 0
    assert span.lo < span.hi
    assert span.lo.tz is not None and str(span.lo.tz) == "UTC"


def test_fold_count_equals_events_contained_in_the_load_span():
    """Freeze 10.1 / D-006: derived at run time, never hard-coded.

    The expectation is rebuilt here from the **raw artifacts with plain pandas**,
    importing nothing from the module under test. An earlier version called
    ``derive_load_span`` and restated the module's own predicate, so a fault in
    the span computation appeared identically on both sides and the assertion
    could not fail. This version reads the CSVs directly, so a wrong ``lo``/``hi``
    -- a dropped ``dup_anomaly`` filter, a bad parse -- makes the two disagree.

    No literal count appears.
    """
    raw_events = pd.read_csv(INVENTORY, parse_dates=["onset", "recovery"])
    onset = raw_events["onset"].dt.tz_localize("UTC")
    recovery = raw_events["recovery"].dt.tz_localize("UTC")

    raw_load = pd.read_csv(LOAD, usecols=["ts_utc", "dup_anomaly"])
    raw_load = raw_load[raw_load["ts_utc"].notna() & ~raw_load["dup_anomaly"]]
    stamps = pd.to_datetime(raw_load["ts_utc"], utc=True)
    lo, hi = stamps.min(), stamps.max()

    expected = int(((onset >= lo) & (recovery <= hi)).sum())

    derived = derive_eligible_events(INVENTORY, LOAD)
    assert derived.fold_count == expected
    assert derived.fold_count == derived.count
    assert derived.fold_count > 0


def test_derived_span_matches_an_independent_recomputation():
    """The span itself must be verifiable without the module that produces it."""
    raw_load = pd.read_csv(LOAD, usecols=["ts_utc", "dup_anomaly"])
    raw_load = raw_load[raw_load["ts_utc"].notna() & ~raw_load["dup_anomaly"]]
    stamps = pd.to_datetime(raw_load["ts_utc"], utc=True)

    span = derive_load_span(LOAD)
    assert span.lo == stamps.min()
    assert span.hi == stamps.max()
    assert span.usable_rows == len(stamps)


def test_eligible_set_is_a_strict_subset_of_the_inventory(eligible):
    """Eligibility must exclude something, and must never invent an event."""
    inventory = load_event_inventory(INVENTORY)
    assert eligible.count < len(inventory)
    assert eligible.inventory_rows == len(inventory)
    assert set(eligible.table["onset"]).issubset(
        set(assign_event_ids(inventory)["onset"])
    )


def test_excluded_events_all_precede_the_load_span(eligible):
    """Excluded events must fall outside the span, not be dropped arbitrarily."""
    inventory = assign_event_ids(load_event_inventory(INVENTORY))
    excluded = inventory[~inventory["event_id"].isin(eligible.event_ids)]
    assert not excluded.empty
    for _, row in excluded.iterrows():
        outside = row["onset"] < eligible.span.lo or row["recovery"] > eligible.span.hi
        assert outside, f"{row['event_id']} was excluded but lies inside the span"


def test_every_eligible_interval_is_fully_covered_by_load(eligible):
    """Full containment must mean complete, unique, non-null hourly coverage."""
    load = pd.read_csv(LOAD, usecols=["ts_utc", "ERCOT", "dup_anomaly"])
    load = load[load["ts_utc"].notna() & ~load["dup_anomaly"]].copy()
    load["ts_utc"] = pd.to_datetime(load["ts_utc"], utc=True)

    for _, event in eligible.table.iterrows():
        inside = load[
            (load["ts_utc"] >= event["onset"]) & (load["ts_utc"] <= event["recovery"])
        ]
        assert len(inside) == int(event["hours"]), (
            f"{event['event_id']}: {len(inside)} load rows vs declared "
            f"{int(event['hours'])} hours"
        )
        assert inside["ts_utc"].is_unique
        assert not inside["ERCOT"].isna().any()


def test_event_ids_follow_the_controlling_convention():
    """E%02d_%Y%m%d, numbered 1-based over the FULL inventory."""
    inventory = assign_event_ids(load_event_inventory(INVENTORY))
    for _, row in inventory.iterrows():
        index = row["event_index"] + 1
        expected = f"E{index:02d}_{row['onset'].strftime('%Y%m%d')}"
        assert row["event_id"] == expected


@pytest.mark.parametrize("event_id", EXPLORATORY_EVENT_IDS)
def test_exploratory_events_exist_and_are_eligible(eligible, event_id):
    """E08, E14, E21 must be present and load-eligible."""
    event = eligible.require(event_id)
    assert int(event["hours"]) > 0
    assert event["recovery"] > event["onset"]


def test_unknown_event_id_is_rejected(eligible):
    with pytest.raises(EligibilityError):
        eligible.require("E99_29990101")


def test_event_hour_index_is_timezone_aware_utc():
    """D-007: event hours carry a real UTC tz, never a fixed offset."""
    index = event_hour_index(INVENTORY, LOAD)
    assert index.tz is not None and str(index.tz) == "UTC"
    assert index.is_monotonic_increasing
    assert not index.has_duplicates


def test_event_hour_index_covers_every_eligible_event(eligible):
    """The stage-3 exclusion index must total the declared event hours."""
    index = event_hour_index(INVENTORY, LOAD)
    assert len(index) == int(eligible.table["hours"].sum())


@pytest.mark.skipif(not CENSORING.is_file(), reason="censoring artifact absent")
def test_inventory_utc_convention_is_corroborated_by_the_censoring_artifact(eligible):
    """The naive-inventory-means-UTC convention must be evidenced, not assumed.

    No adopted decision states the zone of the inventory's naive timestamps.
    The controlling builder localizes them to UTC; if that were wrong, every
    event window would shift and the censoring artifact's ``ts_utc`` values --
    produced by that same builder from the same inventory -- would not line up
    with the onsets derived here.

    This asserts the correspondence directly, so the convention rests on
    controlling evidence rather than on a silent choice in our code.
    """
    censoring = pd.read_csv(CENSORING, usecols=["event_id", "ts_utc"])
    censoring["ts_utc"] = pd.to_datetime(censoring["ts_utc"], utc=True)
    first_hour = censoring.groupby("event_id")["ts_utc"].min()

    for _, event in eligible.table.iterrows():
        assert first_hour[event["event_id"]] == event["onset"], (
            f"{event['event_id']}: censoring artifact starts at "
            f"{first_hour[event['event_id']]} but the inventory onset localizes "
            f"to {event['onset']} -- the UTC convention does not hold"
        )


@pytest.mark.skipif(not CENSORING.is_file(), reason="censoring artifact absent")
def test_censoring_artifact_agrees_as_an_independent_cross_check(eligible):
    """Secondary corroboration only — NOT the acceptance oracle.

    The eligible set above is derived from the inventory and load span alone.
    The censoring artifact was built by the same controlling rule, so agreement
    is expected; disagreement would indicate one of them has drifted.
    """
    censoring = pd.read_csv(CENSORING, usecols=["event_id"])
    assert set(censoring["event_id"]) == set(eligible.event_ids)
    assert len(censoring) == int(eligible.table["hours"].sum())
