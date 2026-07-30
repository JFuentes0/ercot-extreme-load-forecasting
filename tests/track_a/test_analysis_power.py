"""Regression tests for the pre-registered analysis's power calculation.

The minimum detectable effect appears in the headline verdict, in the null
branch of the decision rule, and on the forest plot. A wrong value would
misstate what the study could and could not have seen.

**The bug these guard against was real.** `scipy.stats.nct.cdf` returns NaN for
large non-centrality (ncp above roughly 8-10). NaN fails every `>=` comparison,
so the bisection read "cannot evaluate" as "not enough power" and walked the
answer upward — reporting an MDE of 2.36 on the stage-5 data where the true
value is 0.50, a 4.8x overstatement.

Expectations here come from Monte Carlo and from the analytic normal
approximation, never from the implementation.
"""

from __future__ import annotations

import importlib.util
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "analyze_stage5.py"


def _module():
    spec = importlib.util.spec_from_file_location("analyze_stage5_undertest", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # Registered before exec: @dataclass resolves annotations through
    # sys.modules and raises if the module is not there yet.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def analysis():
    return _module()


@pytest.mark.parametrize("ncp", [0.5, 2.0, 5.0, 9.0, 12.0, 20.0, 40.0])
def test_power_is_finite_at_every_non_centrality(analysis, ncp: float) -> None:
    """Power must be a real number even where the exact CDF gives up.

    This is the guard. `nct.cdf` goes NaN somewhere above ncp ~8; the fallback
    has to cover that range, because the bisection walks straight through it.
    """
    n = 17
    sd = 1.0
    effect = ncp * sd / np.sqrt(n)
    power = analysis._two_sided_power(effect, sd, n)
    assert np.isfinite(power), f"power not finite at ncp={ncp}"
    assert 0.0 <= power <= 1.0


def test_power_is_monotone_in_effect(analysis) -> None:
    """Bisection is only valid if power increases with the effect."""
    n, sd = 17, 0.68
    powers = [analysis._two_sided_power(e, sd, n) for e in np.linspace(0.0, 3.0, 40)]
    assert all(later >= earlier - 1e-9 for earlier, later in pairwise(powers))


@pytest.mark.parametrize("effect", [0.3, 0.5, 0.8])
def test_power_matches_monte_carlo(analysis, effect: float) -> None:
    """Cross-check against simulation of the actual test being run."""
    n, sd = 17, 0.6843
    rng = np.random.default_rng(20260729)
    samples = rng.normal(effect, sd, size=(30000, n))
    simulated = float(
        np.mean(stats.ttest_1samp(samples, popmean=0.0, axis=1).pvalue < 0.05)
    )
    assert analysis._two_sided_power(effect, sd, n) == pytest.approx(
        simulated, abs=0.02
    )


def test_mde_achieves_eighty_percent_power(analysis) -> None:
    """The returned MDE is the effect at which power is 80% — by construction."""
    rng = np.random.default_rng(7)
    values = list(rng.normal(0.46, 0.68, size=17))
    n = len(values)
    mde = analysis._mde(values, n)
    sd = float(np.std(values, ddof=1))
    assert analysis._two_sided_power(mde, sd, n) == pytest.approx(0.80, abs=0.005)


def test_mde_is_near_the_analytic_approximation(analysis) -> None:
    """Sanity bound: the exact MDE sits close to (t_crit + z_power)·se.

    The buggy version returned ~4.8x this, which is exactly the failure mode a
    coarse bound like this one catches.
    """
    values = list(np.random.default_rng(11).normal(0.5, 0.68, size=17))
    n = len(values)
    sd = float(np.std(values, ddof=1))
    approx = (stats.t.ppf(0.975, df=n - 1) + stats.norm.ppf(0.80)) * sd / np.sqrt(n)
    assert analysis._mde(values, n) == pytest.approx(approx, rel=0.10)


def test_mde_shrinks_as_the_sample_grows(analysis) -> None:
    """More events, smaller detectable effect — the whole point of the sweep."""
    rng = np.random.default_rng(3)
    sd = 0.7
    small = analysis._mde(list(rng.normal(0.0, sd, size=5)), 5)
    large = analysis._mde(list(rng.normal(0.0, sd, size=60)), 60)
    assert large < small


def test_mde_is_nan_below_two_observations(analysis) -> None:
    assert np.isnan(analysis._mde([0.4], 1))


def test_verdict_reports_inconclusive_when_the_tests_disagree(analysis) -> None:
    """The pre-registration forbids picking the favourable test."""
    lines = analysis._verdict(mean=0.5, p=0.01, p_wilcoxon=0.30, mde=0.5)
    assert any("INCONCLUSIVE" in line for line in lines)


def test_verdict_null_branch_states_the_mde_and_refuses_to_claim_refutation(
    analysis,
) -> None:
    """A null must carry the MDE and must not read as a failure to replicate."""
    lines = analysis._verdict(mean=0.05, p=0.6, p_wilcoxon=0.6, mde=0.5)
    joined = " ".join(lines)
    assert "NO DETECTABLE DIFFERENCE" in joined
    assert "0.5" in joined
    assert "NEITHER CONFIRMS NOR REFUTES" in joined


@pytest.mark.parametrize(
    ("mean", "expected"),
    [(0.5, "AdaCNP ADVANTAGE"), (-0.5, "CNP ADVANTAGE")],
)
def test_verdict_directions(analysis, mean: float, expected: str) -> None:
    lines = analysis._verdict(mean=mean, p=0.01, p_wilcoxon=0.02, mde=0.2)
    assert any(expected in line for line in lines)
