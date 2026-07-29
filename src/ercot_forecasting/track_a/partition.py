"""Partition and issuance safeguards (workstream 4).

Implements the frozen structural protections:

* **UTC** is the canonical storage, join, partition, and alignment axis (D-007,
  freeze §5).
* **``America/Chicago``** supplies calendar day boundaries and the issuance
  reference, and nothing else. Every conversion goes through the ``zoneinfo``
  database; **no fixed UTC offset is constructed anywhere in this module**.
* Day-ahead issuance is frozen at **09:00 ``America/Chicago`` on D−1**
  (freeze §5, D-007). Only information at or before that instant may enter a
  target-day prediction.
* Outer partitions are **leave-one-event-out**, with a **±7-day buffer** around
  the held-out event excluded from training **and** from context retrieval
  (freeze §3).

Two engineering decisions are recorded here because the frozen design does not
settle them:

**DST target days.** Freeze §6 fixes a 24-hour target vector, while freeze §5
puts day boundaries on the ``America/Chicago`` calendar. A spring-forward day has
23 local hours and a fall-back day 25, so neither can form a 24-hour vector. Such
days are therefore **not usable as target days**. In the adopted artifact this
excludes 49 of 8,947 calendar days. They remain fully available as context and as
training history; only their use as a *target* is excluded.

**Buffer arithmetic.** The ±7-day buffer is applied in UTC as a fixed
``7 * 24`` hour span either side of the event interval. Applying it on the local
calendar would make the buffer 167 or 169 hours across a DST boundary; a fixed
UTC span keeps every fold's exclusion identical in duration. This is a duration
choice, not a timezone conversion, so it does not conflict with D-007.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from ercot_forecasting.track_a.event_eligibility import (
    EligibleEvents,
    derive_eligible_events,
)
from ercot_forecasting.track_a.load_data import (
    CALENDAR_ZONE,
    TARGET_COLUMN,
    load_harmonized,
    local_calendar_day,
)

#: Issuance is 09:00 local on D-1 (freeze §5, D-007).
ISSUANCE_LOCAL_HOUR = 9

#: Buffer either side of a held-out event (freeze §3).
BUFFER_DAYS = 7

#: Hours in a target vector (freeze §6).
HORIZON = 24


class PartitionError(ValueError):
    """Raised when a partition or issuance invariant cannot be satisfied."""


def issuance_cutoff_utc(target_day: date, zone: str = CALENDAR_ZONE) -> pd.Timestamp:
    """The issuance instant for a target day, as a UTC timestamp.

    09:00 on the local calendar day before ``target_day``, resolved through the
    timezone database and converted to UTC. Across a DST boundary the resulting
    UTC hour shifts, which is correct: the *local* issuance time is what is
    frozen, not a fixed offset from UTC.
    """
    previous = target_day - timedelta(days=1)
    local = datetime.combine(previous, time(ISSUANCE_LOCAL_HOUR)).replace(
        tzinfo=ZoneInfo(zone)
    )
    return pd.Timestamp(local).tz_convert("UTC")


def event_window(event: pd.Series) -> tuple[pd.Timestamp, pd.Timestamp]:
    """The event's closed interval, ``onset`` to ``recovery`` inclusive."""
    return event["onset"], event["recovery"]


def buffered_window(
    event: pd.Series, buffer_days: int = BUFFER_DAYS
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """The event interval widened by the buffer on each side (freeze §3)."""
    if buffer_days < 0:
        raise PartitionError(f"buffer_days must be non-negative, got {buffer_days}")
    pad = pd.Timedelta(days=buffer_days)
    return event["onset"] - pad, event["recovery"] + pad


def event_hour_mask(
    stamps: pd.Series, eligible: EligibleEvents, buffer_days: int = 0
) -> pd.Series:
    """Boolean mask marking hours inside any eligible event, optionally buffered.

    With ``buffer_days=0`` this marks exactly the event-period hours that stage 3
    must exclude (D-008, freeze §11.1).
    """
    mask = pd.Series(False, index=stamps.index)
    for _, event in eligible.table.iterrows():
        lo, hi = (
            buffered_window(event, buffer_days) if buffer_days else event_window(event)
        )
        mask |= (stamps >= lo) & (stamps <= hi)
    return mask


@dataclass(frozen=True)
class TargetDayIndex:
    """Target days that can form a complete 24-hour vector."""

    days: tuple[date, ...]
    hours: dict[date, pd.DatetimeIndex]
    excluded_dst_days: tuple[date, ...]
    excluded_incomplete_days: tuple[date, ...]

    def __len__(self) -> int:
        return len(self.days)


def build_target_days(load: pd.DataFrame, zone: str = CALENDAR_ZONE) -> TargetDayIndex:
    """Index the calendar days that yield a complete, non-null 24-hour vector.

    A day qualifies only if it has exactly ``HORIZON`` hourly observations on the
    local calendar and no null target value. DST-transition days are reported
    separately from days excluded for missing data, so the two causes never blur.
    """
    frame = load.copy()
    frame["local_day"] = local_calendar_day(frame["ts_utc"], zone)

    days: list[date] = []
    hours: dict[date, pd.DatetimeIndex] = {}
    dst_excluded: list[date] = []
    incomplete: list[date] = []

    for day, group in frame.groupby("local_day", sort=True):
        if len(group) != HORIZON:
            dst_excluded.append(day)
            continue
        if group[TARGET_COLUMN].isna().any():
            incomplete.append(day)
            continue
        days.append(day)
        hours[day] = pd.DatetimeIndex(group["ts_utc"].sort_values(), name="ts_utc")

    return TargetDayIndex(
        days=tuple(days),
        hours=hours,
        excluded_dst_days=tuple(dst_excluded),
        excluded_incomplete_days=tuple(incomplete),
    )


def issuance_safe_candidates(
    target_day: date,
    candidate_days: tuple[date, ...],
    target_index: TargetDayIndex,
    zone: str = CALENDAR_ZONE,
) -> tuple[date, ...]:
    """Candidate context days whose every hour precedes the issuance cutoff.

    Freeze §3 requires all context days to precede the target issuance time, and
    D-007 permits only information available at or before it. A candidate day
    qualifies only if its **last** hour is strictly before the cutoff, so no part
    of a partially-observed day can leak in.
    """
    cutoff = issuance_cutoff_utc(target_day, zone)
    return tuple(
        day
        for day in candidate_days
        if day != target_day and target_index.hours[day].max() < cutoff
    )


@dataclass(frozen=True)
class Fold:
    """One leave-one-event-out outer fold."""

    event_id: str
    event_index: int
    onset: pd.Timestamp
    recovery: pd.Timestamp
    buffer_lo: pd.Timestamp
    buffer_hi: pd.Timestamp

    def excludes(self, stamp: pd.Timestamp) -> bool:
        """Whether a timestamp falls in this fold's excluded window."""
        return self.buffer_lo <= stamp <= self.buffer_hi


def build_loeo_folds(
    eligible: EligibleEvents, buffer_days: int = BUFFER_DAYS
) -> tuple[Fold, ...]:
    """One outer fold per load-eligible event.

    The fold count is the eligible-event count, derived from the artifacts. No
    literal appears here (D-006, freeze §10.1).
    """
    folds: list[Fold] = []
    for _, event in eligible.table.iterrows():
        lo, hi = buffered_window(event, buffer_days)
        folds.append(
            Fold(
                event_id=str(event["event_id"]),
                event_index=int(event["event_index"]),
                onset=event["onset"],
                recovery=event["recovery"],
                buffer_lo=lo,
                buffer_hi=hi,
            )
        )
    return tuple(folds)


def fold_training_mask(stamps: pd.Series, fold: Fold) -> pd.Series:
    """Hours admissible for training and retrieval within one fold.

    The held-out event **and its buffer** are excluded from both, per freeze §3.
    The same mask governs retrieval, so a context day can never be drawn from
    inside the held-out window.
    """
    return ~((stamps >= fold.buffer_lo) & (stamps <= fold.buffer_hi))


def stage3_target_days(
    load: pd.DataFrame,
    eligible: EligibleEvents,
    zone: str = CALENDAR_ZONE,
) -> tuple[TargetDayIndex, tuple[date, ...]]:
    """Target days usable for stage-3 normal-period validation.

    D-008 restricts stage 3 to non-event periods and requires **every**
    event-period hour to be excluded. A day qualifies only if it forms a complete
    24-hour vector **and** none of its hours falls inside any eligible event.

    Returns the usable index and the days rejected for containing event hours.
    """
    index = build_target_days(load, zone)
    event_hours = set(
        load.loc[event_hour_mask(load["ts_utc"], eligible, buffer_days=0), "ts_utc"]
    )

    usable: list[date] = []
    rejected: list[date] = []
    for day in index.days:
        if event_hours.isdisjoint(set(index.hours[day])):
            usable.append(day)
        else:
            rejected.append(day)

    filtered = TargetDayIndex(
        days=tuple(usable),
        hours={d: index.hours[d] for d in usable},
        excluded_dst_days=index.excluded_dst_days,
        excluded_incomplete_days=index.excluded_incomplete_days,
    )
    return filtered, tuple(rejected)


def build_partition_inputs(
    inventory_path: str | Path,
    load_path: str | Path,
) -> tuple[pd.DataFrame, EligibleEvents, tuple[Fold, ...]]:
    """Convenience assembly of the load frame, eligible events, and LOEO folds."""
    load = load_harmonized(load_path, usable_only=True)
    eligible = derive_eligible_events(inventory_path, load_path)
    folds = build_loeo_folds(eligible)
    return load, eligible, folds
