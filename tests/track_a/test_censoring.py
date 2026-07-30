"""Tests for the censoring artifact and the adopted D-010 treatment.

These read the frozen censoring artifact and assert the states, counts, and
exclusion rule the adopted ruling depends on. No model is built and no
event-period model performance is computed here.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ercot_forecasting.track_a.censoring import (
    UNRESOLVED,
    VERIFIED_NO_SHED,
    VERIFIED_SHED,
    CensoringError,
    load_censoring_index,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CENSORING = REPO_ROOT / "data" / "frozen" / "track_a" / "v7_demand_censored_v3.csv"

pytestmark = pytest.mark.skipif(
    not CENSORING.is_file(), reason="censoring artifact not imported"
)


@pytest.fixture(scope="module")
def censoring():
    return load_censoring_index(CENSORING)


def test_three_states_partition_the_event_record() -> None:
    """Every event-hour carries exactly one of the three recognised states.

    The expectation is rebuilt from the **raw CSV with plain pandas**, importing
    nothing from the module under test. An earlier version summed three counts
    that the loader itself derived from one frame and compared them with that
    frame's length — guaranteed by construction, so it could not fail.
    """
    raw = pd.read_csv(CENSORING)
    counts = raw["censor_status"].value_counts()

    index = load_censoring_index(CENSORING)
    assert index.total_event_hours == len(raw)
    assert index.n_verified_shed == int(counts.get(VERIFIED_SHED, 0))
    assert index.n_unresolved == int(counts.get(UNRESOLVED, 0))
    assert index.n_verified_no_shed == int(counts.get(VERIFIED_NO_SHED, 0))
    assert set(counts.index) <= {VERIFIED_SHED, UNRESOLVED, VERIFIED_NO_SHED}


def test_no_hour_is_verified_no_shed(censoring) -> None:
    """The record contains no affirmative finding of absence of shed.

    D-010 §2 turns on this: treating `unresolved` as uncensored would assert
    exactly the finding that no hour carries.
    """
    assert censoring.n_verified_no_shed == 0


def test_unresolved_is_the_majority_state(censoring) -> None:
    """`unresolved` dominates, which is why D-010 retains rather than drops it."""
    assert censoring.n_unresolved > censoring.n_verified_shed


def test_shed_hours_concentrate_in_one_event(censoring) -> None:
    """Most `verified_shed` hours fall in a single event.

    Derived from the artifact, not asserted against a literal event name, so the
    test states the structural fact without hard-coding the record.
    """
    shed = censoring.frame[censoring.frame["censor_status"] == VERIFIED_SHED]
    largest = shed["event_id"].value_counts().iloc[0]
    assert largest > censoring.n_verified_shed / 2


def test_shed_mask_excludes_only_verified_shed(censoring) -> None:
    """The D-010 exclusion mask marks `verified_shed` hours and nothing else."""
    frame = censoring.frame
    stamps = pd.DatetimeIndex(frame["ts_utc"])
    mask = censoring.shed_mask(stamps)

    assert mask.sum() == censoring.n_verified_shed
    assert (frame.loc[mask, "censor_status"] == VERIFIED_SHED).all()
    assert not (frame.loc[mask, "censor_status"] == UNRESOLVED).any()


def test_unresolved_hours_are_retained_by_the_shed_mask(censoring) -> None:
    """`unresolved` hours survive the primary-metric exclusion (D-010 §3.2)."""
    unresolved = censoring.frame[censoring.frame["censor_status"] == UNRESOLVED]
    mask = censoring.shed_mask(pd.DatetimeIndex(unresolved["ts_utc"]))
    assert not mask.any()


def test_hours_outside_any_event_are_not_treated_as_unresolved(censoring) -> None:
    """An hour absent from the artifact carries no censoring determination."""
    outside = pd.DatetimeIndex(["1990-01-01 00:00:00+00:00"])
    assert not censoring.shed_mask(outside).any()
    assert not censoring.unresolved_mask(outside).any()


def test_per_event_counts_are_derived_not_literal(censoring) -> None:
    """Counts come from the artifact and sum to the event's declared hours."""
    for event_id in censoring.frame["event_id"].unique():
        counts = censoring.counts_for_event(str(event_id))
        assert (
            counts[VERIFIED_SHED] + counts[UNRESOLVED] + counts[VERIFIED_NO_SHED]
            == counts["declared_event_hours"]
        )


def test_unrecognised_state_stops_the_run(tmp_path: Path, censoring) -> None:
    """An unknown censoring state must fail loudly, not be grouped with a known one."""
    corrupted = censoring.frame.head(5).copy()
    corrupted.loc[corrupted.index[0], "censor_status"] = "probably_fine"
    path = tmp_path / "corrupted.csv"
    corrupted.to_csv(path, index=False)

    with pytest.raises(CensoringError, match="unrecognised censoring states"):
        load_censoring_index(path)
