"""Harmonized load artifact loading and validation (workstream 3).

Operates on the artifact adopted by decision **D-009**, identified by content
(SHA-256 ``272af17c…``, 54,688,032 bytes) rather than by filename.

Time handling follows **D-007**: ``ts_utc`` is the canonical axis and is parsed
timezone-aware; ``America/Chicago`` is used only for calendar days and the
issuance cutoff, always through the ``zoneinfo`` timezone database. **No fixed
UTC offset is constructed anywhere in this module** — a spring-forward or
fall-back day is handled by the database, not by arithmetic on a constant.

The module lives under ``track_a/`` rather than ``shared/`` because
``PROJECT_CHARTER.md`` requires any shared-module change to carry tests for both
tracks, and Track B is frozen and not executing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

#: Columns the harmonized artifact is required to carry.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "ts_hb",
    "dst_marked",
    "COAST",
    "EAST",
    "FAR_WEST",
    "NORTH",
    "NORTH_C",
    "SOUTHERN",
    "SOUTH_C",
    "WEST",
    "ERCOT",
    "spring_relabeled",
    "zone_mismatch",
    "occurrence",
    "fold",
    "dup_anomaly",
    "year",
    "source_file",
    "pre_apr2003_restated",
    "ts_utc",
)

#: The forecast target column.
TARGET_COLUMN = "ERCOT"

#: Calendar and issuance reference zone (freeze §5, D-007). Never a fixed offset.
CALENDAR_ZONE = "America/Chicago"


class LoadValidationError(ValueError):
    """Raised when the load artifact violates a required invariant."""


@dataclass(frozen=True)
class LoadValidationReport:
    """Outcome of the workstream-3 checks against the load artifact."""

    path: Path
    total_rows: int
    usable_rows: int
    columns: tuple[str, ...]
    schema_ok: bool
    ts_utc_timezone_aware: bool
    duplicate_timestamps: int
    monotonic: bool
    expected_hours: int
    observed_hours: int
    continuity_gaps: int
    gap_examples: tuple[str, ...]
    missing_target_values: int
    missing_target_examples: tuple[str, ...]
    zone_mismatch_rows: int
    dup_anomaly_rows: int
    pre_apr2003_rows: int
    lo: pd.Timestamp
    hi: pd.Timestamp
    full_local_days: int
    short_local_days: int
    long_local_days: int
    dst_day_examples: tuple[str, ...] = field(default=())

    @property
    def is_clean(self) -> bool:
        """True when every hard invariant holds.

        A missing target value is *reported*, not fatal: stage 3 excludes any
        target day containing one, so the record can be imperfect without
        invalidating the pipeline.
        """
        return (
            self.schema_ok
            and self.ts_utc_timezone_aware
            and self.duplicate_timestamps == 0
            and self.monotonic
            and self.continuity_gaps == 0
        )

    def as_lines(self) -> list[str]:
        return [
            f"path                     {self.path}",
            f"total rows               {self.total_rows:,}",
            f"usable rows              {self.usable_rows:,}  (dup_anomaly dropped)",
            f"schema ok                {self.schema_ok}",
            f"ts_utc timezone-aware    {self.ts_utc_timezone_aware}",
            f"duplicate timestamps     {self.duplicate_timestamps}",
            f"monotonic                {self.monotonic}",
            f"expected hourly slots    {self.expected_hours:,}",
            f"observed hourly slots    {self.observed_hours:,}",
            f"continuity gaps          {self.continuity_gaps}",
            f"missing target values    {self.missing_target_values}",
            f"zone_mismatch rows       {self.zone_mismatch_rows}",
            f"dup_anomaly rows         {self.dup_anomaly_rows}",
            f"pre_apr2003_restated     {self.pre_apr2003_rows:,}",
            f"span                     {self.lo} .. {self.hi}",
            f"full 24-hour local days  {self.full_local_days:,}",
            f"23-hour local days       {self.short_local_days}  (spring forward)",
            f"25-hour local days       {self.long_local_days}  (fall back)",
        ]


def load_harmonized(path: str | Path, usable_only: bool = True) -> pd.DataFrame:
    """Load the harmonized artifact with a timezone-aware UTC axis.

    Args:
        path: the D-009 artifact.
        usable_only: drop rows with a null ``ts_utc`` or ``dup_anomaly`` set,
            matching the controlling builder's filter.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"load artifact not found: {path}")

    frame = pd.read_csv(path, low_memory=False)
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        raise LoadValidationError(f"load artifact missing columns: {missing}")

    if usable_only:
        frame = frame[frame["ts_utc"].notna() & ~frame["dup_anomaly"]].copy()
    frame["ts_utc"] = pd.to_datetime(frame["ts_utc"], utc=True)
    return frame.sort_values("ts_utc").reset_index(drop=True)


def local_calendar_day(timestamps: pd.Series, zone: str = CALENDAR_ZONE) -> pd.Series:
    """Map UTC timestamps to their ``America/Chicago`` calendar date.

    Conversion goes through the timezone database. D-007 prohibits fixed
    offsets, so no constant is ever added here.
    """
    return timestamps.dt.tz_convert(ZoneInfo(zone)).dt.date


def validate_load_artifact(
    path: str | Path, zone: str = CALENDAR_ZONE
) -> LoadValidationReport:
    """Run the workstream-3 validation checks and return a report.

    Covers schema and columns, duplicate-timestamp detection, monotonic UTC
    ordering, timezone-aware conversion, hourly continuity including DST
    transitions, and missing values.
    """
    path = Path(path)
    raw = pd.read_csv(path, low_memory=False)
    schema_ok = list(raw.columns) == list(REQUIRED_COLUMNS)

    frame = load_harmonized(path, usable_only=True)
    stamps = frame["ts_utc"]

    lo, hi = stamps.min(), stamps.max()
    expected = int((hi - lo) / pd.Timedelta(hours=1)) + 1
    observed = len(stamps)

    full_axis = pd.date_range(lo, hi, freq="h", tz="UTC")
    gaps = full_axis.difference(pd.DatetimeIndex(stamps))

    missing_mask = frame[TARGET_COLUMN].isna()
    missing_examples = tuple(str(t) for t in frame.loc[missing_mask, "ts_utc"].head(5))

    days = local_calendar_day(stamps, zone)
    per_day = days.value_counts()
    dst_days = sorted(str(d) for d in per_day[per_day != 24].index)

    return LoadValidationReport(
        path=path,
        total_rows=len(raw),
        usable_rows=len(frame),
        columns=tuple(raw.columns),
        schema_ok=schema_ok,
        ts_utc_timezone_aware=stamps.dt.tz is not None,
        duplicate_timestamps=int(stamps.duplicated().sum()),
        monotonic=bool(stamps.is_monotonic_increasing),
        expected_hours=expected,
        observed_hours=observed,
        continuity_gaps=len(gaps),
        gap_examples=tuple(str(t) for t in gaps[:5]),
        missing_target_values=int(missing_mask.sum()),
        missing_target_examples=missing_examples,
        zone_mismatch_rows=int(raw["zone_mismatch"].sum()),
        dup_anomaly_rows=int(raw["dup_anomaly"].sum()),
        pre_apr2003_rows=int(raw["pre_apr2003_restated"].sum()),
        lo=lo,
        hi=hi,
        full_local_days=int((per_day == 24).sum()),
        short_local_days=int((per_day == 23).sum()),
        long_local_days=int((per_day == 25).sum()),
        dst_day_examples=tuple(dst_days[:5]),
    )
