"""Issuance-safe feature construction for real-data episodes.

An episode targets one calendar day ``D`` and predicts its 24-hour load vector
(freeze §3, §6). Every input feature must be available at or before **09:00
``America/Chicago`` on D−1** (freeze §5, D-007).

Feature set for stage 3 — calendar plus load history, **no weather**:

* **Calendar** (5): cyclic day-of-year, cyclic day-of-week, weekend flag. These
  are properties of the target date itself and are known arbitrarily far ahead,
  so they carry no issuance risk.
* **Recent load** (24): the last 24 *complete* hourly observations strictly
  preceding the issuance cutoff.

Weather is deliberately absent. `EXPERIMENT_FREEZE_v1.md` §3 permits weather but
mandates no feature table, and the corpus contains only *realized* weather —
no day-ahead forecast product with historical issuance timestamps. Using
realized target-day weather would breach the issuance cutoff; using it with a
truncation rule requires decisions that stage 3 does not need. See
`/tmp/TRACK_A_IMPORT_QUESTIONS_REVIEW.md`.

Hour-completeness convention: ``ts_utc`` is hour-*beginning*, so the row stamped
``t`` covers ``[t, t+1h)`` and is complete only at ``t+1h``. A row is therefore
available at the cutoff iff ``t + 1h <= cutoff``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from ercot_forecasting.track_a.load_data import CALENDAR_ZONE, TARGET_COLUMN
from ercot_forecasting.track_a.partition import (
    HORIZON,
    TargetDayIndex,
    issuance_cutoff_utc,
)

#: Number of trailing complete hours used as the load-history feature.
LAG_HOURS = 24

#: Calendar feature names, in order.
CALENDAR_FEATURES: tuple[str, ...] = (
    "doy_sin",
    "doy_cos",
    "dow_sin",
    "dow_cos",
    "is_weekend",
)

#: Total input dimension.
FEATURE_DIM = len(CALENDAR_FEATURES) + LAG_HOURS


class FeatureError(ValueError):
    """Raised when a feature vector cannot be built safely."""


@dataclass(frozen=True)
class EpisodeArrays:
    """Per-day feature and target arrays, aligned by row."""

    days: tuple[date, ...]
    x: np.ndarray  # (n_days, FEATURE_DIM)
    y: np.ndarray  # (n_days, HORIZON)
    cutoffs: np.ndarray  # (n_days,) issuance cutoff, UTC

    def __len__(self) -> int:
        return len(self.days)


def calendar_features(day: date) -> np.ndarray:
    """Cyclic calendar features for a target date.

    Known in advance for any date, so they cannot breach the issuance cutoff.
    """
    doy = day.timetuple().tm_yday
    dow = day.weekday()
    return np.array(
        [
            np.sin(2.0 * np.pi * doy / 365.25),
            np.cos(2.0 * np.pi * doy / 365.25),
            np.sin(2.0 * np.pi * dow / 7.0),
            np.cos(2.0 * np.pi * dow / 7.0),
            1.0 if dow >= 5 else 0.0,
        ],
        dtype=np.float64,
    )


def build_episode_arrays(
    load: pd.DataFrame,
    target_index: TargetDayIndex,
    zone: str = CALENDAR_ZONE,
) -> EpisodeArrays:
    """Build issuance-safe ``x`` and 24-hour ``y`` for every usable target day.

    A day is dropped if fewer than ``LAG_HOURS`` complete observations precede
    its cutoff, or if any of them is null — the early days of the record cannot
    supply a full lag window.
    """
    frame = load.sort_values("ts_utc").reset_index(drop=True)
    # Both sides of the search are already UTC, so dropping the tz marker for
    # the numpy comparison is exact -- it is a representation change, not a
    # timezone conversion, and introduces no offset arithmetic (D-007).
    stamps = (
        frame["ts_utc"]
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
        .to_numpy("datetime64[ns]")
    )
    values = frame[TARGET_COLUMN].to_numpy(dtype=np.float64)

    days: list[date] = []
    rows_x: list[np.ndarray] = []
    rows_y: list[np.ndarray] = []
    cutoffs: list[pd.Timestamp] = []

    hour = np.timedelta64(1, "h")

    for day in target_index.days:
        cutoff = issuance_cutoff_utc(day, zone)
        # Row t is complete at t+1h, so it is available iff t + 1h <= cutoff.
        limit = np.datetime64(cutoff.tz_convert("UTC").tz_localize(None)) - hour
        end = int(np.searchsorted(stamps, limit, side="right"))
        if end < LAG_HOURS:
            continue

        lag = values[end - LAG_HOURS : end]
        if np.isnan(lag).any():
            continue

        target_hours = target_index.hours[day]
        target = frame.loc[frame["ts_utc"].isin(target_hours), TARGET_COLUMN].to_numpy(
            dtype=np.float64
        )
        if target.shape[0] != HORIZON or np.isnan(target).any():
            continue

        days.append(day)
        rows_x.append(np.concatenate([calendar_features(day), lag]))
        rows_y.append(target)
        cutoffs.append(cutoff.tz_convert("UTC").tz_localize(None))

    if not days:
        raise FeatureError("no target day produced a complete feature vector")

    return EpisodeArrays(
        days=tuple(days),
        x=np.vstack(rows_x),
        y=np.vstack(rows_y),
        cutoffs=np.array(cutoffs, dtype="datetime64[ns]"),
    )


@dataclass(frozen=True)
class Normalizer:
    """Standardisation fitted on the outer training partition only.

    Track A rules require every tensor normalization to be fitted on the outer
    training partition. Fitting on all days would leak validation-period
    statistics into the model's inputs.
    """

    x_mean: np.ndarray
    x_std: np.ndarray
    y_mean: float
    y_std: float

    @classmethod
    def fit(cls, x: np.ndarray, y: np.ndarray) -> Normalizer:
        x_std = x.std(axis=0)
        x_std[x_std < 1e-8] = 1.0
        y_std = float(y.std())
        return cls(
            x_mean=x.mean(axis=0),
            x_std=x_std,
            y_mean=float(y.mean()),
            y_std=y_std if y_std > 1e-8 else 1.0,
        )

    def transform_x(self, x: np.ndarray) -> np.ndarray:
        return (x - self.x_mean) / self.x_std

    def transform_y(self, y: np.ndarray) -> np.ndarray:
        return (y - self.y_mean) / self.y_std

    def inverse_y(self, y: np.ndarray) -> np.ndarray:
        return y * self.y_std + self.y_mean
