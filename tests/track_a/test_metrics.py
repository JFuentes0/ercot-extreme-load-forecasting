"""Tests for the freeze §7 secondary metrics.

Each expectation is derived **independently of the implementation** — from
adaptive quadrature, from scipy, or from an analytic invariant. Nothing is
compared against a value the module itself produced.

The metrics are descriptive (freeze §7: they "do not adjudicate the
comparison"), but they will appear in the deliverable, so a wrong one would
mislead a reader even though it cannot flip the primary result.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import integrate, stats

from ercot_forecasting.track_a.metrics import (
    COVERAGE_LEVEL,
    SecondaryMetrics,
    cold_context_weight,
    effective_context_count,
    exceedance_probability,
    gaussian_crps,
    interval_covers,
    interval_width,
    summarize,
    weight_entropy,
)


@pytest.mark.parametrize(
    ("mu", "sigma", "y"),
    [
        (0.0, 1.0, 0.0),
        (0.0, 1.0, 1.5),
        (2.0, 0.5, 1.0),
        (-1.0, 3.0, 4.0),
        (5.0, 0.1, 5.3),
        (0.0, 2.0, -6.0),
    ],
)
def test_crps_matches_its_defining_integral(mu: float, sigma: float, y: float) -> None:
    """CRPS = ∫ (F(x) − 1{x ≥ y})² dx, by adaptive quadrature.

    The integrand has a kink at ``y``, so the break point is declared to the
    integrator; a naive uniform grid disagrees in the fifth decimal purely from
    discretisation and would make this test look like a failure.
    """
    got = gaussian_crps(np.array([y]), np.array([mu]), np.array([sigma]))[0]

    def integrand(x: float) -> float:
        return (stats.norm.cdf(x, mu, sigma) - (1.0 if x >= y else 0.0)) ** 2

    expected, _err = integrate.quad(
        integrand, mu - 20 * sigma, mu + 20 * sigma, points=[y], limit=400
    )
    assert got == pytest.approx(expected, abs=1e-10)


def test_crps_is_minimised_by_the_truth_and_never_negative() -> None:
    """Basic score properties: non-negative, and worse as the mean drifts off."""
    y = np.array([0.0])
    sigma = np.array([1.0])
    at_truth = gaussian_crps(y, np.array([0.0]), sigma)[0]
    off = gaussian_crps(y, np.array([2.0]), sigma)[0]
    assert at_truth >= 0.0
    assert at_truth < off


def test_coverage_of_a_calibrated_forecast_hits_the_nominal_level() -> None:
    """A correctly specified Gaussian covers at its nominal rate."""
    rng = np.random.default_rng(0)
    draws = rng.standard_normal(400_000)
    covered = interval_covers(draws, np.zeros_like(draws), np.ones_like(draws))
    assert covered.mean() == pytest.approx(COVERAGE_LEVEL, abs=2e-3)


def test_interval_width_matches_the_normal_quantile() -> None:
    """Width is 2·z_{0.95}·sigma, with z from scipy rather than our constant."""
    z = stats.norm.ppf(0.95)
    got = interval_width(np.array([1.0, 2.5]))
    assert got == pytest.approx(np.array([2 * z, 2 * z * 2.5]), rel=1e-9)


def test_exceedance_probability_matches_the_survival_function() -> None:
    got = exceedance_probability(1.0, np.array([0.0]), np.array([1.0]))[0]
    assert got == pytest.approx(stats.norm.sf(1.0), rel=1e-12)


@pytest.mark.parametrize("n", [2, 4, 64])
def test_uniform_weights_give_maximum_entropy(n: int) -> None:
    """Entropy of a uniform weighting is log n, and effective count is n.

    This is the CNP invariant: its aggregation is uniform by construction, so
    these two values pin what the metric must report for the baseline arm.
    """
    weights = np.full((1, n), 1.0 / n)
    assert weight_entropy(weights)[0] == pytest.approx(math.log(n), rel=1e-12)
    assert effective_context_count(weights)[0] == pytest.approx(n, rel=1e-9)


def test_point_mass_has_zero_entropy_and_one_effective_context() -> None:
    weights = np.zeros((1, 8))
    weights[0, 0] = 1.0
    assert weight_entropy(weights)[0] == pytest.approx(0.0, abs=1e-12)
    assert effective_context_count(weights)[0] == pytest.approx(1.0, rel=1e-9)


def test_entropy_is_bounded_by_log_n_for_arbitrary_weights() -> None:
    rng = np.random.default_rng(3)
    raw = rng.random((200, 16))
    weights = raw / raw.sum(axis=1, keepdims=True)
    assert np.all(weight_entropy(weights) <= math.log(16) + 1e-12)
    assert np.all(effective_context_count(weights) <= 16 + 1e-9)


def test_cold_context_weight_equals_the_cold_fraction_under_uniform_weights() -> None:
    """Under uniform weighting the metric reduces to the cold share.

    This is why the informative quantity is AdaCNP's value *relative to* CNP's:
    CNP's is fixed by the context composition, not by anything it learned.
    """
    weights = np.full((1, 8), 0.125)
    cold = np.zeros((1, 8))
    cold[0, :2] = 1.0
    assert cold_context_weight(weights, cold)[0] == pytest.approx(0.25)


def test_cold_context_weight_detects_concentration_on_cold_days() -> None:
    """All weight on cold days gives 1.0; none gives 0.0."""
    cold = np.zeros((1, 4))
    cold[0, :2] = 1.0
    all_cold = np.array([[0.5, 0.5, 0.0, 0.0]])
    none_cold = np.array([[0.0, 0.0, 0.5, 0.5]])
    assert cold_context_weight(all_cold, cold)[0] == pytest.approx(1.0)
    assert cold_context_weight(none_cold, cold)[0] == pytest.approx(0.0)


def test_cold_context_weight_rejects_mismatched_shapes() -> None:
    with pytest.raises(ValueError, match="must match"):
        cold_context_weight(np.ones((1, 4)), np.ones((1, 5)))


def test_summarize_reports_rmse_mae_against_hand_values() -> None:
    target = np.array([1.0, 2.0, 3.0])
    mean = np.array([1.5, 2.0, 1.0])
    scale = np.array([1.0, 1.0, 1.0])
    got = summarize(target, mean, scale, high_load_threshold=10.0)

    errors = target - mean  # [-0.5, 0.0, 2.0]
    assert got.rmse == pytest.approx(math.sqrt((0.25 + 0.0 + 4.0) / 3))
    assert got.mae == pytest.approx((0.5 + 0.0 + 2.0) / 3)
    assert got.coverage_deviation == pytest.approx(abs(got.coverage - COVERAGE_LEVEL))
    assert np.mean(np.abs(errors)) == pytest.approx(got.mae)


def test_summarize_omits_weight_metrics_when_no_weights_supplied() -> None:
    """The three AdaCNP-internal metrics are None, not zero, when undefined.

    Reporting zero would read as "no weight on cold days", which is a finding.
    Absent is not zero.
    """
    got = summarize(
        np.array([0.0]), np.array([0.0]), np.array([1.0]), high_load_threshold=1.0
    )
    assert got.weight_entropy is None
    assert got.effective_context_count is None
    assert got.cold_context_weight is None
    assert isinstance(got, SecondaryMetrics)


def test_summarize_omits_cold_share_when_weights_exist_but_temperature_does_not() -> (
    None
):
    """base feature set: weights are available, cold days are not identifiable."""
    got = summarize(
        np.array([0.0]),
        np.array([0.0]),
        np.array([1.0]),
        high_load_threshold=1.0,
        weights=np.full((1, 4), 0.25),
    )
    assert got.weight_entropy == pytest.approx(math.log(4))
    assert got.cold_context_weight is None


def test_exceedance_is_reported_both_observed_and_predicted() -> None:
    """Both sides are needed: the metric is a tail-calibration comparison."""
    target = np.array([0.0, 0.0, 5.0, 5.0])
    mean = np.zeros(4)
    scale = np.ones(4)
    got = summarize(target, mean, scale, high_load_threshold=2.0)
    assert got.observed_exceedance == pytest.approx(0.5)
    assert got.predicted_exceedance == pytest.approx(stats.norm.sf(2.0), rel=1e-9)
    assert got.high_load_threshold == pytest.approx(2.0)


def test_all_twelve_reported_keys_are_present() -> None:
    """The manifest schema is stable: every key exists even when the value is None."""
    got = summarize(
        np.array([0.0]), np.array([0.0]), np.array([1.0]), high_load_threshold=1.0
    ).as_dict()
    assert set(got) == {
        "crps",
        "rmse",
        "mae",
        "interval_width_90",
        "empirical_coverage_90",
        "coverage_deviation_abs",
        "high_load_threshold_normalized",
        "observed_high_load_exceedance",
        "predicted_high_load_exceedance",
        "adacnp_weight_entropy_nats",
        "effective_context_count",
        "cold_context_weight_share",
    }
