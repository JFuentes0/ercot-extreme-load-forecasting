"""Censoring states and the adopted D-010 treatment.

Reads the frozen V7 censoring artifact and exposes the three states the record
distinguishes, so that scoring code never has to interpret censoring evidence
for itself.

The adopted ruling is `docs/track_a/CENSORING_TREATMENT_RULING_v1.md` (decision
**D-010**):

* ``verified_shed`` hours are **excluded** from the primary latent-demand NLL.
  Served load in those hours is an established lower bound on latent demand, so
  scoring a Gaussian likelihood against it estimates served load, not demand.
* ``unresolved`` hours are **retained and flagged**. Unknown is not censored and
  is not verified-uncensored; the ruling forbids defaulting them either way.
* An all-hours **served-load** NLL is a **required** secondary diagnostic, whose
  estimand is served load rather than latent demand.

Every state is read from the artifact at run time. No hour's status is
hard-coded, and no event or fold count appears here as a literal (D-006,
freeze §10.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

#: The censoring states the V7 artifact distinguishes.
VERIFIED_SHED = "verified_shed"
UNRESOLVED = "unresolved"
VERIFIED_NO_SHED = "verified_no_shed"

KNOWN_STATES: tuple[str, ...] = (VERIFIED_SHED, UNRESOLVED, VERIFIED_NO_SHED)

#: Columns the censoring artifact is required to carry.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "ts_utc",
    "event_id",
    "censor_status",
    "censor_window_id",
    "source_status",
)


class CensoringError(ValueError):
    """Raised when the censoring artifact violates a required invariant."""


@dataclass(frozen=True)
class CensoringIndex:
    """Per-hour censoring state, keyed by UTC timestamp.

    Hours absent from the artifact are outside every declared event window and
    carry no censoring determination at all. They are **not** ``unresolved`` —
    ``unresolved`` is a statement about an event hour whose status was
    investigated and not established. Absent hours are ordinary observations.
    """

    frame: pd.DataFrame
    shed_hours: frozenset[pd.Timestamp]
    unresolved_hours: frozenset[pd.Timestamp]

    @property
    def total_event_hours(self) -> int:
        return len(self.frame)

    @property
    def n_verified_shed(self) -> int:
        return len(self.shed_hours)

    @property
    def n_unresolved(self) -> int:
        return len(self.unresolved_hours)

    @property
    def n_verified_no_shed(self) -> int:
        return int((self.frame["censor_status"] == VERIFIED_NO_SHED).sum())

    def counts_for_event(self, event_id: str) -> dict[str, int]:
        """Per-state hour counts for one event, derived from the artifact."""
        subset = self.frame[self.frame["event_id"] == event_id]
        return {
            "declared_event_hours": len(subset),
            VERIFIED_SHED: int((subset["censor_status"] == VERIFIED_SHED).sum()),
            UNRESOLVED: int((subset["censor_status"] == UNRESOLVED).sum()),
            VERIFIED_NO_SHED: int((subset["censor_status"] == VERIFIED_NO_SHED).sum()),
        }

    def shed_mask(self, stamps: np.ndarray | pd.DatetimeIndex) -> np.ndarray:
        """Boolean mask marking hours that D-010 excludes from the primary NLL.

        ``True`` marks a ``verified_shed`` hour. Every other hour — including
        every ``unresolved`` hour and every hour outside a declared event — is
        retained.
        """
        index = pd.DatetimeIndex(stamps)
        if index.tz is None:
            index = index.tz_localize("UTC")
        else:
            index = index.tz_convert("UTC")
        return np.array([ts in self.shed_hours for ts in index], dtype=bool)

    def unresolved_mask(self, stamps: np.ndarray | pd.DatetimeIndex) -> np.ndarray:
        """Boolean mask marking retained-but-flagged ``unresolved`` hours."""
        index = pd.DatetimeIndex(stamps)
        if index.tz is None:
            index = index.tz_localize("UTC")
        else:
            index = index.tz_convert("UTC")
        return np.array([ts in self.unresolved_hours for ts in index], dtype=bool)


def load_censoring_index(path: str | Path) -> CensoringIndex:
    """Load the frozen censoring artifact and index it by UTC hour.

    Raises:
        CensoringError: if a required column is missing, if a timestamp is
            duplicated, or if an unrecognised censoring state appears. An
            unrecognised state must stop the run rather than be silently
            grouped with a known one.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"censoring artifact not found: {path}")

    frame = pd.read_csv(path, low_memory=False)
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        raise CensoringError(f"censoring artifact missing columns: {missing}")

    frame["ts_utc"] = pd.to_datetime(frame["ts_utc"], utc=True)
    if frame["ts_utc"].duplicated().any():
        raise CensoringError("censoring artifact contains duplicate timestamps")

    unknown = set(frame["censor_status"].unique()) - set(KNOWN_STATES)
    if unknown:
        raise CensoringError(f"unrecognised censoring states: {sorted(unknown)}")

    shed = frame.loc[frame["censor_status"] == VERIFIED_SHED, "ts_utc"]
    unresolved = frame.loc[frame["censor_status"] == UNRESOLVED, "ts_utc"]

    return CensoringIndex(
        frame=frame,
        shed_hours=frozenset(shed),
        unresolved_hours=frozenset(unresolved),
    )
