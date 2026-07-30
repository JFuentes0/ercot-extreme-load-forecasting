"""Issuance-safe feature construction for real-data episodes.

An episode targets one calendar day ``D`` and predicts its 24-hour load vector
(freeze §3, §6). Every input feature must be available at or before **09:00
``America/Chicago`` on D−1** (freeze §5, D-007).

Two feature sets are supported. Both are issuance-safe; the temperature block is
optional so the pair can be run as an ablation.

**Base (29)** — calendar plus load history:

* **Calendar** (5): cyclic day-of-year, cyclic day-of-week, weekend flag. These
  are properties of the target date itself and are known arbitrarily far ahead,
  so they carry no issuance risk.
* **Recent load** (24): the last 24 *complete* hourly observations strictly
  preceding the issuance cutoff.

**With temperature (57)** — adds the block described in `weather.py` (D-012):

* **Recent temperature** (24): the last 24 complete regional-temperature hours
  before the cutoff.
* **Derived** (4): ``roll24`` at the cutoff — the 24-hour rolling mean that the
  controlling event inventory's ``peak_val`` is drawn from — plus heating
  degrees, cooling degrees, and a squared term, standing in for the "non-linear
  functions of the temperatures" among Hu et al.'s PJM inputs.

Stages 3 and 4 originally ran the base set only. That was a divergence from the
frozen design: `EXPERIMENT_FREEZE_v1.md` §3 contemplates weather among the
retrieval inputs, and the events themselves are defined by a temperature
quantity the model could not observe. D-012 records the correction and the
evidence for the artifact's identity.

**No forecast temperature is used.** The corpus holds no day-ahead forecast
product with historical issuance timestamps, so every temperature feature here
is *past-observed* only. Hu et al. additionally use the next day's temperature
forecast for PJM; Track A's temperature features are weaker by exactly that, and
`docs/track_a/REPLICATION_FIDELITY_v1.md` records the gap.

Hour-completeness convention: ``ts_utc`` is hour-*beginning*, so the row stamped
``t`` covers ``[t, t+1h)`` and is complete only at ``t+1h``. A row is therefore
available at the cutoff iff ``t + 1h <= cutoff``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from ercot_forecasting.track_a.load_data import CALENDAR_ZONE, TARGET_COLUMN
from ercot_forecasting.track_a.partition import (
    HORIZON,
    TargetDayIndex,
    issuance_cutoff_utc,
)
from ercot_forecasting.track_a.weather import RegionalTemperature

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

#: Input dimension without temperature — the original Track A feature set.
FEATURE_DIM = len(CALENDAR_FEATURES) + LAG_HOURS

#: Trailing complete temperature hours, matching the load lag length.
TEMP_LAG_HOURS = 24

#: Derived temperature terms appended after the temperature lags, in order.
#: ``roll24`` is the 24-hour rolling mean that the event inventory's ``peak_val``
#: is drawn from, so it is the variable the event definition itself uses. The
#: heating/cooling terms are the "non-linear functions of the temperatures" that
#: Hu et al. list among their PJM inputs.
TEMP_DERIVED_FEATURES: tuple[str, ...] = (
    "roll24_at_cutoff",
    "heating_degrees",
    "cooling_degrees",
    "temp_last_squared",
)

#: Reference temperature for the heating/cooling split, °C (≈65 °F).
COMFORT_TEMP_C = 18.0

#: Input dimension with temperature features present.
FEATURE_DIM_WITH_TEMPERATURE = FEATURE_DIM + TEMP_LAG_HOURS + len(TEMP_DERIVED_FEATURES)


def feature_dim(with_temperature: bool) -> int:
    """Input width for the configured feature set.

    Prefer reading ``EpisodeArrays.x.shape[1]`` where an array is in hand; this
    exists for the places that must size a model before building episodes.
    """
    return FEATURE_DIM_WITH_TEMPERATURE if with_temperature else FEATURE_DIM


def temperature_features(temp_lag: np.ndarray, roll24_at_cutoff: float) -> np.ndarray:
    """Temperature block: the lag window, then the derived terms.

    All inputs are observations complete **before** the issuance cutoff. No
    forecast value is used, and no target-day temperature is read — doing so
    would breach the cutoff (D-007, freeze §5).
    """
    last = float(temp_lag[-1])
    return np.concatenate(
        [
            temp_lag,
            np.array(
                [
                    roll24_at_cutoff,
                    max(0.0, COMFORT_TEMP_C - last),
                    max(0.0, last - COMFORT_TEMP_C),
                    last * last,
                ],
                dtype=np.float64,
            ),
        ]
    )


class FeatureError(ValueError):
    """Raised when a feature vector cannot be built safely."""


@dataclass(frozen=True)
class EpisodeArrays:
    """Per-day feature and target arrays, aligned by row.

    ``rejected`` records every candidate day that was dropped and why, so a
    caller can distinguish an expected shortfall (the first days of the record
    cannot supply a full lag window) from a systematic failure. Dropping days
    silently would make the two indistinguishable.
    """

    days: tuple[date, ...]
    x: np.ndarray  # (n_days, FEATURE_DIM)
    y: np.ndarray  # (n_days, HORIZON)
    cutoffs: np.ndarray  # (n_days,) issuance cutoff, UTC
    rejected: dict[date, str] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.days)

    def select(self, days: tuple[date, ...]) -> EpisodeArrays:
        """Return the subset for ``days``, preserving row alignment.

        A day's features and target depend only on the load frame, never on the
        partition, so the arrays are built **once** over every usable day and
        sliced per fold. Rebuilding them per fold recomputes identical values.
        """
        position = {day: i for i, day in enumerate(self.days)}
        missing = [d for d in days if d not in position]
        if missing:
            raise FeatureError(
                f"{len(missing)} requested day(s) have no episode row, "
                f"first {missing[0]}"
            )
        rows = np.array([position[d] for d in days], dtype=np.int64)
        return EpisodeArrays(
            days=days,
            x=self.x[rows],
            y=self.y[rows],
            cutoffs=self.cutoffs[rows],
            rejected=self.rejected,
        )


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
    temperature: RegionalTemperature | None = None,
) -> EpisodeArrays:
    """Build issuance-safe ``x`` and 24-hour ``y`` for every usable target day.

    A day is dropped if fewer than ``LAG_HOURS`` complete observations precede
    its cutoff, or if any of them is null — the early days of the record cannot
    supply a full lag window. Every drop is recorded in ``rejected``.

    Passing ``temperature`` appends the temperature block (D-012), closing the
    largest divergence from Hu et al., whose PJM inputs include past-day
    temperature and non-linear functions of it. The argument is optional so the
    temperature-free feature set remains runnable as an ablation — the two
    together measure what the temperature axis contributes.
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

    temp_stamps = temperature.stamps if temperature is not None else None
    temp_values = temperature.temp_c if temperature is not None else None
    temp_roll24 = temperature.roll24 if temperature is not None else None

    days: list[date] = []
    rows_x: list[np.ndarray] = []
    rows_y: list[np.ndarray] = []
    cutoffs: list[pd.Timestamp] = []
    rejected: dict[date, str] = {}

    hour = np.timedelta64(1, "h")

    for day in target_index.days:
        cutoff = issuance_cutoff_utc(day, zone)
        # Row t is complete at t+1h, so it is available iff t + 1h <= cutoff.
        limit = np.datetime64(cutoff.tz_convert("UTC").tz_localize(None)) - hour
        end = int(np.searchsorted(stamps, limit, side="right"))
        if end < LAG_HOURS:
            rejected[day] = "lag window incomplete at the issuance cutoff"
            continue

        lag = values[end - LAG_HOURS : end]
        if np.isnan(lag).any():
            rejected[day] = "null value inside the lag window"
            continue

        # Locate the day's own hours by position on the sorted axis rather than
        # by a full-frame membership test. The frame is sorted and the day's
        # hours are known, so a searchsorted plus a slice is exact -- and ~237x
        # cheaper than scanning every row once per day.
        target_hours = target_index.hours[day]
        first = np.datetime64(target_hours.min().tz_convert("UTC").tz_localize(None))
        start = int(np.searchsorted(stamps, first, side="left"))
        stop = start + HORIZON
        if stop > len(stamps):
            rejected[day] = "target day runs past the end of the record"
            continue

        # Verifying the slice against the day's own stamps is strictly stronger
        # than checking its length: it also catches a gap in the hourly axis,
        # which a positional slice would otherwise span silently.
        expected = (
            target_hours.tz_convert("UTC").tz_localize(None).to_numpy("datetime64[ns]")
        )
        if not np.array_equal(stamps[start:stop], expected):
            rejected[day] = "hourly axis does not match the day's expected hours"
            continue

        target = values[start:stop]
        if np.isnan(target).any():
            rejected[day] = "null target value"
            continue

        blocks = [calendar_features(day), lag]

        if temperature is not None:
            assert temp_stamps is not None  # narrowed by the guard above
            assert temp_values is not None
            assert temp_roll24 is not None
            # Same completeness rule as load: a temperature hour stamped t is
            # complete at t+1h, so it is available iff t + 1h <= cutoff.
            t_end = int(np.searchsorted(temp_stamps, limit, side="right"))
            if t_end < TEMP_LAG_HOURS:
                rejected[day] = "temperature lag window incomplete at the cutoff"
                continue
            temp_lag = temp_values[t_end - TEMP_LAG_HOURS : t_end]
            roll_at_cutoff = temp_roll24[t_end - 1]
            if np.isnan(temp_lag).any() or np.isnan(roll_at_cutoff):
                rejected[day] = "null value inside the temperature lag window"
                continue
            blocks.append(temperature_features(temp_lag, float(roll_at_cutoff)))

        days.append(day)
        rows_x.append(np.concatenate(blocks))
        rows_y.append(target)
        cutoffs.append(cutoff.tz_convert("UTC").tz_localize(None))

    if not days:
        raise FeatureError("no target day produced a complete feature vector")

    return EpisodeArrays(
        days=tuple(days),
        x=np.vstack(rows_x),
        y=np.vstack(rows_y),
        cutoffs=np.array(cutoffs, dtype="datetime64[ns]"),
        rejected=rejected,
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
