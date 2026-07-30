"""The frozen experimental constants have one source of truth.

`configs/track_a/exploratory_stage4_runs.yaml` transcribes several constants that
live authoritatively in `partition.py` and `load_data.py`. Those transcriptions
are for readability — the runner does not read most of them — which means they
could drift from the modules with nothing to catch it. This module is that
catch.

It also guards the derived constants that were *stored* as independent literals
and so could silently contradict the rule they came from. `MIN_CONTEXT_LAG_DAYS`
is one; the stage-4 lag span was another, and it was wrong by 14 hours until
`stage4.episode_lag_start` began deriving it.

Placed under `tests/shared/` because these constants govern both tracks. It
imports no model code, so it is safe for Track B (`PROJECT_CHARTER.md`).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest
import yaml

from ercot_forecasting.track_a.features import LAG_HOURS
from ercot_forecasting.track_a.load_data import CALENDAR_ZONE
from ercot_forecasting.track_a.partition import (
    BUFFER_DAYS,
    HORIZON,
    ISSUANCE_LOCAL_HOUR,
    issuance_cutoff_utc,
)
from ercot_forecasting.track_a.stage3 import MIN_CONTEXT_LAG_DAYS
from ercot_forecasting.track_a.stage4 import episode_lag_start

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN = REPO_ROOT / "configs" / "track_a" / "exploratory_stage4_runs.yaml"


@pytest.fixture(scope="module")
def plan() -> dict:
    return yaml.safe_load(PLAN.read_text(encoding="utf-8"))


def test_yaml_transcriptions_equal_the_module_constants(plan: dict) -> None:
    """The config's frozen values match the modules that actually govern them."""
    assert plan["horizon"] == HORIZON
    assert plan["buffer_days"] == BUFFER_DAYS
    assert plan["issuance_calendar_zone"] == CALENDAR_ZONE
    assert plan["canonical_axis"] == "UTC"

    hour, minute = plan["issuance_local_time"].split(":")
    assert int(hour) == ISSUANCE_LOCAL_HOUR
    assert int(minute) == 0, "a non-zero issuance minute is not modelled anywhere"


def test_min_context_lag_follows_from_the_issuance_rule() -> None:
    """`MIN_CONTEXT_LAG_DAYS` is derivable, and equals the stored literal.

    The rule: a candidate context day qualifies only if its last hour precedes
    the target's cutoff. With the cutoff at 09:00 local on D−1 and a day's last
    hour beginning at 23:00 local, D−1 cannot qualify and D−2 is the newest that
    can. If the issuance hour ever moved past 23:00, the stored constant would
    be wrong; this test would fail rather than let that pass.
    """
    assert ISSUANCE_LOCAL_HOUR < 23, (
        "with issuance at or after 23:00 local, D-1 could qualify as context "
        "and MIN_CONTEXT_LAG_DAYS would no longer be 2"
    )
    assert MIN_CONTEXT_LAG_DAYS == 2


@pytest.mark.parametrize(
    "day",
    [
        date(2011, 2, 2),  # CST
        date(2021, 2, 16),  # CST
        date(2015, 7, 15),  # CDT
        date(2024, 3, 11),  # day after spring forward
        date(2024, 11, 4),  # day after fall back
    ],
)
def test_episode_lag_start_is_derived_from_the_cutoff(day: date) -> None:
    """The lag span is `cutoff − LAG_HOURS`, and reaches well past 25 hours.

    Regression guard on a real defect: the span was once computed as
    ``first_hour − (LAG_HOURS + 1)``, which understated the reach by ~15 hours
    because the cutoff precedes the target day by that much. That admitted
    training days whose features drew on the held-out buffered window.
    """
    cutoff = issuance_cutoff_utc(day)
    assert episode_lag_start(day) == cutoff - pd.Timedelta(hours=LAG_HOURS)

    first_hour = pd.Timestamp(day, tz=CALENDAR_ZONE).tz_convert("UTC")
    reach = first_hour - episode_lag_start(day)
    assert reach > pd.Timedelta(hours=LAG_HOURS + 1), (
        "the lag reaches further back than the naive first-hour span; that gap "
        "is exactly the defect this test guards"
    )
    assert reach >= pd.Timedelta(hours=38)


def test_lag_and_horizon_agree_with_the_frozen_day(plan: dict) -> None:
    """Both the target vector and the lag window are one calendar day long."""
    assert HORIZON == 24
    assert LAG_HOURS == HORIZON
    assert plan["horizon"] == HORIZON


def test_seeds_are_the_three_frozen_seeds(plan: dict) -> None:
    """Freeze §8 fixes three seeds, in order, shared by both arms."""
    assert plan["seeds"] == [20260729, 20260730, 20260731]


def test_context_conditions_and_feature_sets_are_recognised(plan: dict) -> None:
    """The config only names axes the code implements (D-012, D-013)."""
    from ercot_forecasting.track_a.context_conditions import ContextCondition

    for name in plan["context_conditions"]:
        assert ContextCondition(name)
    assert set(plan["feature_sets"]) <= {"base", "temperature"}
