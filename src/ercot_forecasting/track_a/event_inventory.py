"""Controlling event-inventory loading and validation.

Operates on the artifact adopted by decision **D-006**,
`event_inventory_headline.csv`, imported to `data/shared/`.

Two rules from the governing record shape this module and are enforced, not
assumed:

**D-006 — counts are derived, never hard-coded.** No event count or fold count
appears as a literal here. :func:`event_count` reads the artifact.

**D-007 — fixed UTC offsets are prohibited, and no timezone may be inferred.**
The controlling inventory carries **no timezone designator** in any column, and
no accompanying schema file states one (`ARTIFACT_INVENTORY_001.md` §8.2). This
module therefore loads the timestamps as **naive** and
:func:`localize_inventory` **refuses** to convert them until a caller supplies
an explicit IANA zone. It will not guess, and it will not apply a constant
offset.

This module lives under `track_a/` rather than `shared/` deliberately: per
`PROJECT_CHARTER.md`, any shared-module change requires tests for both tracks, and Track
B is frozen and not being executed by this task.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

#: Columns the controlling inventory is required to carry, in order.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "onset",
    "recovery",
    "peak",
    "peak_val",
    "hours",
    "season",
    "margin_C",
)

#: Timestamp-bearing columns.
TIMESTAMP_COLUMNS: tuple[str, ...] = ("onset", "recovery", "peak")


class InventoryValidationError(ValueError):
    """Raised when the controlling inventory violates a required invariant."""


@dataclass(frozen=True)
class InventoryReport:
    """Result of validating the controlling inventory."""

    path: Path
    event_count: int
    columns: tuple[str, ...]
    timezone_declared: bool
    duplicate_onsets: int
    onsets_monotonic: bool
    non_positive_durations: int
    earliest_onset: pd.Timestamp
    latest_recovery: pd.Timestamp

    def as_lines(self) -> list[str]:
        return [
            f"path                  {self.path}",
            f"event_count (derived) {self.event_count}",
            f"columns               {', '.join(self.columns)}",
            f"timezone_declared     {self.timezone_declared}",
            f"duplicate_onsets      {self.duplicate_onsets}",
            f"onsets_monotonic      {self.onsets_monotonic}",
            f"non_positive_duration {self.non_positive_durations}",
            f"earliest_onset        {self.earliest_onset}",
            f"latest_recovery       {self.latest_recovery}",
        ]


def load_event_inventory(path: str | Path) -> pd.DataFrame:
    """Load the controlling inventory with naive timestamps.

    Timestamps are deliberately left timezone-naive. The artifact declares no
    zone; inferring one would violate D-007. Use :func:`localize_inventory` with
    an explicit zone once a ruling supplies it.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"event inventory not found: {path}")

    frame = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        raise InventoryValidationError(
            f"inventory is missing required columns: {missing}"
        )
    for column in TIMESTAMP_COLUMNS:
        frame[column] = pd.to_datetime(frame[column], errors="raise")
        if frame[column].dt.tz is not None:
            raise InventoryValidationError(
                f"column {column!r} unexpectedly carries a timezone; the "
                "controlling artifact declares none"
            )
    return frame


def event_count(frame: pd.DataFrame) -> int:
    """Derive the event count from the artifact.

    D-006 and freeze §10.1 forbid hard-coding this value. It is read here and
    nowhere asserted as a literal.
    """
    return len(frame)


def timezone_is_declared(frame: pd.DataFrame) -> bool:
    """Whether the artifact declares a timezone. Currently expected ``False``."""
    return any(frame[column].dt.tz is not None for column in TIMESTAMP_COLUMNS)


def localize_inventory(frame: pd.DataFrame, zone: str) -> pd.DataFrame:
    """Localize naive inventory timestamps to an explicit IANA zone, then UTC.

    Args:
        frame: inventory loaded by :func:`load_event_inventory`.
        zone: an IANA zone name, e.g. ``"America/Chicago"``. A fixed offset such
            as ``"UTC-06:00"`` is rejected: D-007 requires DST to be handled by a
            timezone database, not a constant offset.

    Raises:
        InventoryValidationError: if ``zone`` is not a usable IANA zone name.

    Note:
        This function is provided so that, once a ruling states the inventory's
        zone, conversion is a single explicit call. It is **not** called anywhere
        by default, because no ruling currently states that zone.
    """
    # Reject offset-shaped strings such as "UTC-06:00" or "GMT+6": D-007
    # requires DST to come from a timezone database, not a constant. Bare "UTC"
    # is a legitimate IANA zone and is permitted -- it is the convention the
    # controlling builder uses for these timestamps (see
    # event_eligibility.INVENTORY_NAIVE_ZONE).
    if not zone or re.fullmatch(r"(?i)(utc|gmt)[+-]\d{1,2}(:\d{2})?", zone.strip()):
        raise InventoryValidationError(
            f"{zone!r} is a fixed offset, not an IANA zone name; fixed offsets "
            "are prohibited by D-007"
        )
    try:
        tzinfo = ZoneInfo(zone)
    except Exception as exc:  # surfaced as a domain error
        raise InventoryValidationError(f"unknown IANA zone {zone!r}") from exc

    out = frame.copy()
    for column in TIMESTAMP_COLUMNS:
        out[column] = out[column].dt.tz_localize(tzinfo).dt.tz_convert("UTC")
    return out


def validate_event_inventory(path: str | Path) -> InventoryReport:
    """Run the inventory checks required by the readiness contract.

    Covers, for this artifact: schema and column validation, duplicate-timestamp
    detection, monotonic ordering, and a timezone-declaration check.
    """
    path = Path(path)
    frame = load_event_inventory(path)

    onsets = frame["onset"]
    duplicate_onsets = int(onsets.duplicated().sum())
    onsets_monotonic = bool(onsets.is_monotonic_increasing)
    durations = frame["recovery"] - frame["onset"]
    non_positive = int((durations <= pd.Timedelta(0)).sum())

    if duplicate_onsets:
        raise InventoryValidationError(
            f"{duplicate_onsets} duplicate onset timestamps in {path}"
        )
    if non_positive:
        raise InventoryValidationError(
            f"{non_positive} events have recovery at or before onset in {path}"
        )

    return InventoryReport(
        path=path,
        event_count=event_count(frame),
        columns=tuple(frame.columns),
        timezone_declared=timezone_is_declared(frame),
        duplicate_onsets=duplicate_onsets,
        onsets_monotonic=onsets_monotonic,
        non_positive_durations=non_positive,
        earliest_onset=onsets.min(),
        latest_recovery=frame["recovery"].max(),
    )
