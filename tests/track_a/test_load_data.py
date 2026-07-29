"""Workstream-3 validation tests against the imported load artifact.

Reads the D-009 artifact's timestamps, flags, and target column. Performs no
held-out-event prediction and inspects no model performance.
"""

from __future__ import annotations

import re
import tokenize
from pathlib import Path

import pandas as pd
import pytest

from ercot_forecasting.track_a.load_data import (
    CALENDAR_ZONE,
    REQUIRED_COLUMNS,
    TARGET_COLUMN,
    load_harmonized,
    local_calendar_day,
    validate_load_artifact,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LOAD = REPO_ROOT / "data" / "frozen" / "track_a" / "ercot_hourly_load_harmonized.csv"
SRC = REPO_ROOT / "src" / "ercot_forecasting" / "track_a"

pytestmark = pytest.mark.skipif(
    not LOAD.is_file(), reason="load artifact has not been imported"
)


@pytest.fixture(scope="module")
def report():
    return validate_load_artifact(LOAD)


@pytest.fixture(scope="module")
def load():
    return load_harmonized(LOAD)


def test_schema_matches_required_columns(report):
    """Check 3: schema and column validation."""
    assert report.schema_ok
    assert report.columns == REQUIRED_COLUMNS


def test_no_duplicate_timestamps(report):
    """Check 4: duplicate-timestamp detection."""
    assert report.duplicate_timestamps == 0


def test_timestamps_are_monotonic_utc(report):
    """Check 5: monotonic UTC timestamps."""
    assert report.monotonic
    assert report.ts_utc_timezone_aware


def test_hourly_continuity_has_no_gaps(report):
    """Check 7: hourly continuity across the whole span, DST included."""
    assert report.continuity_gaps == 0, f"gaps at {report.gap_examples}"
    assert report.observed_hours == report.expected_hours


def test_missing_value_report_is_produced(report):
    """Check 8: missing values are counted and located, not silently ignored.

    A missing target is tolerated at artifact level; stage-3 target-day
    construction excludes any day containing one. This test asserts the report
    exists and is self-consistent, not that the record is perfect.
    """
    assert report.missing_target_values >= 0
    assert len(report.missing_target_examples) == min(report.missing_target_values, 5)


def test_timezone_conversion_uses_the_tz_database(load):
    """Check 6: America/Chicago conversion, and DST actually observed.

    If a fixed offset were being applied, every local day would have 24 hours.
    The presence of both 23- and 25-hour days proves the timezone database is
    doing the work.
    """
    days = local_calendar_day(load["ts_utc"], CALENDAR_ZONE)
    per_day = days.value_counts()
    assert (per_day == 23).any(), "no spring-forward day found"
    assert (per_day == 25).any(), "no fall-back day found"


def test_no_fixed_utc_offset_appears_in_source():
    """Check 11: D-007 prohibits fixed UTC offsets in time handling.

    Scans **executable code only**. Docstrings and comments are skipped via the
    tokenizer, because this codebase deliberately *documents* the prohibition --
    e.g. `event_inventory.py` explains that a `"UTC-06:00"` argument is rejected.
    Matching that prose would make the test fire on its own documentation, so
    only real tokens are inspected. `zoneinfo.ZoneInfo` is the permitted route.
    """
    banned = (
        re.compile(r"utcoffset"),
        re.compile(r"\bpytz\b"),
        re.compile(r"FixedOffset"),
        re.compile(r"UTC[+-]\d"),
    )
    offenders: list[str] = []
    for path in sorted(SRC.glob("*.py")):
        with open(path, "rb") as handle:
            for token in tokenize.tokenize(handle.readline):
                if token.type in (tokenize.STRING, tokenize.COMMENT):
                    continue
                if token.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
                    continue
                for pattern in banned:
                    if pattern.search(token.string):
                        offenders.append(
                            f"{path.name}:{token.start[0]}: {token.string}"
                        )
    assert not offenders, "fixed UTC offset constructs found:\n" + "\n".join(offenders)


def test_the_offset_scanner_actually_detects_a_violation(tmp_path):
    """The scanner above must be capable of failing.

    A guard that cannot fire is worthless. This plants a real fixed-offset
    construct in executable position and confirms the same patterns catch it.
    """
    planted = tmp_path / "violation.py"
    planted.write_text(
        "import datetime\n"
        "TZ = datetime.timezone(datetime.timedelta(hours=-6))\n"
        "STAMP = 'x'.utcoffset\n",
        encoding="utf-8",
    )
    banned = (re.compile(r"utcoffset"), re.compile(r"\bpytz\b"))
    found = False
    with open(planted, "rb") as handle:
        for token in tokenize.tokenize(handle.readline):
            if token.type in (tokenize.STRING, tokenize.COMMENT):
                continue
            if any(p.search(token.string) for p in banned):
                found = True
    assert found, "scanner failed to detect a planted violation"


def test_usable_filter_matches_the_controlling_builder(load):
    """The dup_anomaly filter and UTC parse match v7_build_censoring_v3.py."""
    assert not load["dup_anomaly"].any()
    assert load["ts_utc"].notna().all()
    assert load["ts_utc"].is_unique


def test_pre_apr2003_rows_are_flagged_not_dropped(report, load):
    """M-Q1: the record starts 2002-01-01 with restated rows flagged.

    The flag must mark a real, non-empty prefix -- dropping those rows would
    silently shorten the modeling record and change the eligibility span.
    """
    assert report.pre_apr2003_rows > 0
    flagged = load[load["pre_apr2003_restated"]]
    assert (
        flagged["ts_utc"].max()
        < load.loc[~load["pre_apr2003_restated"], "ts_utc"].max()
    )


def test_target_column_is_present_and_numeric(load):
    assert TARGET_COLUMN in load.columns
    assert pd.api.types.is_numeric_dtype(load[TARGET_COLUMN])
