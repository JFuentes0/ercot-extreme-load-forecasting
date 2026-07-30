"""Regional temperature index (decision **D-012**).

Loads `data/frozen/track_a/regional_index.parquet`, the ERCOT regional
temperature index carrying an hourly ``regional_temp_c`` and its 24-hour
rolling mean ``roll24``.

**Provenance — why this artifact and not another.** This file is the
definitional basis of the controlling event inventory adopted by D-006: every
one of the inventory's ``peak_val`` entries equals this artifact's ``roll24``
at the corresponding ``peak`` timestamp, verified for all inventory rows and
asserted by `tests/track_a/test_weather.py`. Importing it therefore does not
introduce a new data source into Track A — it imports the source the frozen
event definition already depends on.

**Timezone semantics.** The parquet index is timezone-**naive**. It is
interpreted as UTC, on the same basis and by the same reasoning as
`event_eligibility.INVENTORY_NAIVE_ZONE`: the 21/21 ``peak_val`` correspondence
establishes that this artifact and the inventory share one convention, and the
inventory's UTC reading is independently corroborated against the censoring
artifact's explicit ``ts_utc``. No adopted decision states the convention in
words for either file; D-012 records the inference and the evidence for it.
No fixed UTC offset is constructed anywhere here (D-007).

**Issuance safety.** These are *realized* observations, not forecasts. Only
values complete at or before the 09:00 ``America/Chicago`` D−1 cutoff may enter
a target-day feature vector; `features.build_episode_arrays` enforces that with
the same `searchsorted` bound it applies to load. A next-day temperature
forecast — which Hu et al. use for PJM — does not exist in this corpus, so
Track A's temperature features are strictly *past-observed* and are weaker than
the paper's by that much.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

#: The hourly regional temperature column.
TEMP_COLUMN = "regional_temp_c"

#: Its 24-hour rolling mean — the quantity the event inventory's `peak_val` is.
ROLL24_COLUMN = "roll24"

REQUIRED_COLUMNS: tuple[str, ...] = (TEMP_COLUMN, ROLL24_COLUMN)

#: The naive parquet index is read as UTC. See the module docstring.
INDEX_NAIVE_ZONE = "UTC"


class WeatherError(ValueError):
    """Raised when the temperature artifact violates a required invariant."""


@dataclass(frozen=True)
class RegionalTemperature:
    """Hourly regional temperature on a timezone-aware UTC axis."""

    stamps: np.ndarray  # datetime64[ns], naive-UTC, sorted
    temp_c: np.ndarray
    roll24: np.ndarray
    path: Path

    def __len__(self) -> int:
        return len(self.stamps)

    @property
    def span(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        lo = pd.Timestamp(self.stamps[0]).tz_localize(INDEX_NAIVE_ZONE)
        hi = pd.Timestamp(self.stamps[-1]).tz_localize(INDEX_NAIVE_ZONE)
        return lo, hi

    @property
    def missing_temp(self) -> int:
        return int(np.isnan(self.temp_c).sum())

    @property
    def missing_roll24(self) -> int:
        return int(np.isnan(self.roll24).sum())


def load_regional_temperature(path: str | Path) -> RegionalTemperature:
    """Load the regional temperature index, validated and UTC-ordered.

    Raises:
        WeatherError: on a missing column, a duplicated timestamp, or a
            non-monotonic axis. Each would silently corrupt a lag window rather
            than fail, so all three stop the run.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"regional temperature artifact not found: {path}")

    frame = pd.read_parquet(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        raise WeatherError(f"temperature artifact missing columns: {missing}")

    index = pd.DatetimeIndex(frame.index)
    if index.tz is not None:
        index = index.tz_convert(INDEX_NAIVE_ZONE).tz_localize(None)
    if index.duplicated().any():
        raise WeatherError("temperature artifact contains duplicate timestamps")
    if not index.is_monotonic_increasing:
        raise WeatherError("temperature artifact is not monotonically ordered")

    return RegionalTemperature(
        stamps=index.to_numpy("datetime64[ns]"),
        temp_c=frame[TEMP_COLUMN].to_numpy(dtype=np.float64),
        roll24=frame[ROLL24_COLUMN].to_numpy(dtype=np.float64),
        path=path,
    )
