"""Load-eligible event derivation and LOEO fold counting.

Implements the **pre-existing load-eligibility rule** that decision D-006 refers
to. That rule was located in executable form in the hash-verified controlling
builder ``v7_build_censoring_v3.py`` (SHA-256 ``c07898bc…``, a member of the
13-item declared controlling set), lines 223-241:

    ev["onset"]    = ev.onset.dt.tz_localize("UTC")
    ev["recovery"] = ev.recovery.dt.tz_localize("UTC")
    load = load[load.ts_utc.notna() & ~load.dup_anomaly]
    assert load.ts_utc.is_unique
    lo, hi = load.ts_utc.min(), load.ts_utc.max()
    elig = ev[(ev.onset >= lo) & (ev.recovery <= hi)]

So an inventory event is load-eligible **iff its closed interval is fully
contained in the usable load span**. Event hours are the closed interval
``onset <= ts_utc <= recovery`` — inclusive of both endpoints, which is why the
inventory's ``hours`` column equals elapsed hours plus one.

Two properties this module deliberately preserves:

**Counts are derived, never hard-coded** (D-006, freeze §10.1). No event count
or fold count appears as a literal anywhere here.

**Eligibility is computed from the governing inputs, not read from a downstream
artifact.** An earlier draft of this module derived the eligible set by reading
``event_id`` out of ``v7_demand_censored_v3.csv``. That agreed only because the
censoring artifact was itself built by this rule; it inherited the answer instead
of computing it, could not detect a changed load span, and made a stage-4 gating
artifact a dependency of stage-3 fold construction. The censoring artifact is now
used only as an optional independent cross-check.

The naive inventory timestamps are localized to **UTC**, matching the controlling
builder. This uses no fixed offset and is consistent with D-007.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ercot_forecasting.track_a.event_inventory import load_event_inventory

#: Load columns required to derive the usable span.
REQUIRED_LOAD_COLUMNS: tuple[str, ...] = ("ts_utc", "dup_anomaly")

#: Zone the inventory's naive timestamps are interpreted in.
#:
#: The controlling builder ``v7_build_censoring_v3.py`` localizes them with
#: ``tz_localize("UTC")``, and the resulting windows reproduce the imported
#: censoring artifact's ``ts_utc`` values exactly -- e.g. E05's onset
#: ``2004-12-23 13:00:00`` becomes ``2004-12-23 13:00:00+00:00``, which is the
#: first hour that artifact records for E05. ``test_inventory_utc_convention_is_
#: corroborated_by_the_censoring_artifact`` asserts that correspondence, so the
#: choice is evidenced rather than assumed.
#:
#: This is a bare IANA zone, not a fixed offset, so it satisfies D-007. **No
#: adopted decision states the convention in words**; it is inferred from
#: controlling code and corroborated by a controlling artifact. Recording it in
#: a decision would remove the last inference here.
INVENTORY_NAIVE_ZONE = "UTC"


class EligibilityError(ValueError):
    """Raised when the eligibility derivation is inconsistent or unusable."""


@dataclass(frozen=True)
class LoadSpan:
    """The usable load span, and the filtering that produced it."""

    lo: pd.Timestamp
    hi: pd.Timestamp
    usable_rows: int
    axis_is_unique: bool


@dataclass(frozen=True)
class EligibleEvents:
    """The derived load-eligible modeling events."""

    table: pd.DataFrame
    span: LoadSpan
    inventory_rows: int

    @property
    def count(self) -> int:
        """Number of load-eligible events, derived from the artifacts."""
        return len(self.table)

    @property
    def fold_count(self) -> int:
        """LOEO fold count: one outer fold per load-eligible event."""
        return self.count

    @property
    def event_ids(self) -> tuple[str, ...]:
        return tuple(self.table["event_id"])

    def require(self, event_id: str) -> pd.Series:
        """Return one event, or raise if it is absent or ineligible."""
        match = self.table.loc[self.table["event_id"] == event_id]
        if match.empty:
            raise EligibilityError(
                f"{event_id!r} is not a load-eligible event in the derived set"
            )
        return match.iloc[0]


def assign_event_ids(inventory: pd.DataFrame) -> pd.DataFrame:
    """Attach ``event_index`` and ``event_id`` using the controlling convention.

    ``event_index`` is the 0-based position in onset order. ``event_id`` is
    ``E%02d_%Y%m%d`` where the number is ``event_index + 1`` — a **1-based
    ordinal over the full inventory**, including events that are not
    load-eligible. Identifiers are therefore stable only while the adopted
    inventory is unchanged.
    """
    out = inventory.reset_index(drop=True).copy()

    # The controlling builder assigns event_index from CSV file order, not from
    # a sort. Re-sorting here would silently rebind every identifier if a future
    # artifact were not already onset-ordered, so the ordering is asserted
    # instead of imposed.
    if not out["onset"].is_monotonic_increasing:
        raise EligibilityError(
            "inventory rows are not in ascending onset order; the controlling "
            "builder assigns event_index from file order, so re-ordering here "
            "would rebind every event_id"
        )

    if out["onset"].dt.tz is None:
        out["onset"] = out["onset"].dt.tz_localize(INVENTORY_NAIVE_ZONE)
        out["recovery"] = out["recovery"].dt.tz_localize(INVENTORY_NAIVE_ZONE)
    out["event_index"] = out.index
    out["event_id"] = [
        f"E{i + 1:02d}_{stamp.strftime('%Y%m%d')}"
        for i, stamp in zip(out.index, out["onset"], strict=True)
    ]
    return out


def derive_load_span(load_path: str | Path) -> LoadSpan:
    """Derive the usable load span exactly as the controlling builder does.

    Drops rows with a null ``ts_utc`` or ``dup_anomaly`` set, parses ``ts_utc``
    as timezone-aware UTC, and requires the resulting axis to be unique.
    """
    load_path = Path(load_path)
    if not load_path.is_file():
        raise FileNotFoundError(f"load artifact not found: {load_path}")

    load = pd.read_csv(load_path, usecols=list(REQUIRED_LOAD_COLUMNS))
    load = load[load["ts_utc"].notna() & ~load["dup_anomaly"]].copy()
    load["ts_utc"] = pd.to_datetime(load["ts_utc"], utc=True)

    unique = bool(load["ts_utc"].is_unique)
    if not unique:
        raise EligibilityError(
            "non-unique UTC axis in the load artifact; the controlling builder "
            "asserts uniqueness before deriving the span"
        )
    return LoadSpan(
        lo=load["ts_utc"].min(),
        hi=load["ts_utc"].max(),
        usable_rows=len(load),
        axis_is_unique=unique,
    )


def derive_eligible_events(
    inventory_path: str | Path,
    load_path: str | Path,
) -> EligibleEvents:
    """Derive the load-eligible event set from the governing artifacts.

    Args:
        inventory_path: the D-006 controlling event inventory.
        load_path: the D-009 controlling harmonized load artifact.

    An event is eligible iff ``onset >= lo`` and ``recovery <= hi``.
    """
    inventory = assign_event_ids(load_event_inventory(inventory_path))
    span = derive_load_span(load_path)

    eligible = inventory[
        (inventory["onset"] >= span.lo) & (inventory["recovery"] <= span.hi)
    ].copy()

    columns = ["event_id", "event_index", "onset", "recovery", "peak", "hours"]
    return EligibleEvents(
        table=eligible[columns].reset_index(drop=True),
        span=span,
        inventory_rows=len(inventory),
    )


def event_hours(load_path: str | Path, event: pd.Series) -> pd.DatetimeIndex:
    """Every load timestamp inside one event's closed interval.

    Uses ``onset <= ts_utc <= recovery``, inclusive of both endpoints, matching
    the controlling builder.
    """
    load = pd.read_csv(load_path, usecols=list(REQUIRED_LOAD_COLUMNS))
    load = load[load["ts_utc"].notna() & ~load["dup_anomaly"]].copy()
    load["ts_utc"] = pd.to_datetime(load["ts_utc"], utc=True)
    inside = load[
        (load["ts_utc"] >= event["onset"]) & (load["ts_utc"] <= event["recovery"])
    ]
    return pd.DatetimeIndex(inside["ts_utc"].sort_values(), name="ts_utc")


def event_hour_index(
    inventory_path: str | Path,
    load_path: str | Path,
) -> pd.DatetimeIndex:
    """Every event-period hour across all load-eligible events, as UTC.

    Stage 3 must exclude every one of these hours (D-008, freeze §11.1). Derived
    from the governing artifacts rather than from the censoring artifact.
    """
    eligible = derive_eligible_events(inventory_path, load_path)

    load = pd.read_csv(load_path, usecols=list(REQUIRED_LOAD_COLUMNS))
    load = load[load["ts_utc"].notna() & ~load["dup_anomaly"]].copy()
    load["ts_utc"] = pd.to_datetime(load["ts_utc"], utc=True)

    mask = pd.Series(False, index=load.index)
    for _, event in eligible.table.iterrows():
        mask |= (load["ts_utc"] >= event["onset"]) & (
            load["ts_utc"] <= event["recovery"]
        )
    return pd.DatetimeIndex(load.loc[mask, "ts_utc"].sort_values(), name="ts_utc")
