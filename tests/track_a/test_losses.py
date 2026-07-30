"""Tests for the primary metric (freeze §7).

`gaussian_nll` is the quantity that adjudicates the whole CNP-versus-AdaCNP
comparison, and it had **no test coverage at all** until this module: no test
file imported `losses.py`. The training smoke tests only assert that loss
decreases, which holds for many incorrect losses — a sign error, a dropped
``0.5``, or treating the scale as a variance would all have passed the suite.

Every expectation here is computed **independently** of the implementation:
either from `math` by hand, or from `scipy.stats.norm.logpdf`. Nothing is
compared against a value produced by the code under test.
"""

from __future__ import annotations

import math

import pytest
import torch

from ercot_forecasting.track_a.losses import gaussian_nll


def _hand_nll(y: float, mu: float, sigma: float) -> float:
    """Gaussian NLL for one scalar, written out longhand.

    −log N(y | mu, sigma²) = ½·log(2π) + log(sigma) + (y−mu)² / (2·sigma²)
    """
    return (
        0.5 * math.log(2.0 * math.pi)
        + math.log(sigma)
        + (y - mu) ** 2 / (2.0 * sigma**2)
    )


def _t(value: float) -> torch.Tensor:
    return torch.tensor([[[value]]], dtype=torch.float64)


def test_matches_closed_form_at_the_standard_normal_mode() -> None:
    """At y = mu and sigma = 1 the NLL is exactly ½·log(2π)."""
    got = float(gaussian_nll(_t(0.0), _t(0.0), _t(1.0)))
    assert got == pytest.approx(0.5 * math.log(2.0 * math.pi), rel=0, abs=1e-12)


@pytest.mark.parametrize(
    ("y", "mu", "sigma"),
    [
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 1.0),
        (-2.5, 0.75, 2.0),
        (10.0, 10.0, 0.25),
        (3.0, -3.0, 0.5),
        (0.1, 0.2, 1e-3),
    ],
)
def test_matches_hand_computed_closed_form(y: float, mu: float, sigma: float) -> None:
    """Elementwise value equals the longhand formula across the parameter range."""
    got = float(gaussian_nll(_t(y), _t(mu), _t(sigma)))
    assert got == pytest.approx(_hand_nll(y, mu, sigma), rel=1e-12)


def test_matches_scipy_logpdf() -> None:
    """Cross-check against an independent implementation.

    Skipped rather than failed if scipy is absent — the hand-computed checks
    above already pin the value; this is corroboration from a second source.
    """
    scipy_stats = pytest.importorskip("scipy.stats")
    y = torch.tensor([[[-1.5, 0.0, 2.25, 7.5]]], dtype=torch.float64)
    mu = torch.tensor([[[0.5, 0.0, 2.0, 6.0]]], dtype=torch.float64)
    sigma = torch.tensor([[[1.0, 3.0, 0.5, 2.5]]], dtype=torch.float64)

    got = gaussian_nll(y, mu, sigma, reduction="none").numpy().ravel()
    expected = -scipy_stats.norm.logpdf(
        y.numpy().ravel(), loc=mu.numpy().ravel(), scale=sigma.numpy().ravel()
    )
    assert got == pytest.approx(expected, rel=1e-12)


def test_scale_is_a_standard_deviation_not_a_variance() -> None:
    """The decoder emits a scale; the loss must square it (MODEL_MECHANICS §4.5).

    Distinguishes the two conventions: at sigma = 2 the correct NLL uses
    variance 4. A loss that treated the scale as the variance would give a
    different, identifiable number.
    """
    y, mu, sigma = 1.0, 0.0, 2.0
    got = float(gaussian_nll(_t(y), _t(mu), _t(sigma)))

    as_std = _hand_nll(y, mu, sigma)  # variance = sigma**2 = 4
    as_variance = (
        0.5 * math.log(2.0 * math.pi)
        + 0.5 * math.log(sigma)
        + (y - mu) ** 2 / (2 * sigma)
    )
    assert got == pytest.approx(as_std, rel=1e-12)
    assert got != pytest.approx(as_variance, rel=1e-6)


def test_larger_error_costs_more_and_the_mode_is_the_minimum() -> None:
    """Monotone in |y − mu|, minimised at y = mu. Catches a sign error."""
    mu, sigma = 0.0, 1.0
    at_mode = float(gaussian_nll(_t(mu), _t(mu), _t(sigma)))
    near = float(gaussian_nll(_t(0.5), _t(mu), _t(sigma)))
    far = float(gaussian_nll(_t(4.0), _t(mu), _t(sigma)))
    assert at_mode < near < far


def test_wider_scale_is_penalised_when_the_prediction_is_perfect() -> None:
    """With y = mu, NLL grows with sigma — the calibration term is present."""
    tight = float(gaussian_nll(_t(0.0), _t(0.0), _t(0.5)))
    wide = float(gaussian_nll(_t(0.0), _t(0.0), _t(4.0)))
    assert tight < wide


def test_reduction_mean_is_the_mean_of_elementwise() -> None:
    y = torch.tensor([[[0.0, 1.0, -2.0]]], dtype=torch.float64)
    mu = torch.tensor([[[0.5, 0.5, 0.5]]], dtype=torch.float64)
    sigma = torch.tensor([[[1.0, 2.0, 0.5]]], dtype=torch.float64)

    elementwise = [
        _hand_nll(0.0, 0.5, 1.0),
        _hand_nll(1.0, 0.5, 2.0),
        _hand_nll(-2.0, 0.5, 0.5),
    ]
    assert float(gaussian_nll(y, mu, sigma, reduction="mean")) == pytest.approx(
        sum(elementwise) / 3.0, rel=1e-12
    )
    assert float(gaussian_nll(y, mu, sigma, reduction="sum")) == pytest.approx(
        sum(elementwise), rel=1e-12
    )
    none = gaussian_nll(y, mu, sigma, reduction="none")
    assert none.shape == y.shape
    assert none.numpy().ravel() == pytest.approx(elementwise, rel=1e-12)


def test_shape_mismatch_is_rejected() -> None:
    y = torch.zeros((2, 1, 3))
    mu = torch.zeros((2, 1, 4))
    with pytest.raises(ValueError, match="must share a shape"):
        gaussian_nll(y, mu, torch.ones((2, 1, 3)))


@pytest.mark.parametrize("bad_scale", [0.0, -1.0])
def test_non_positive_scale_is_rejected(bad_scale: float) -> None:
    """A zero or negative scale is a defect, not something to clamp silently."""
    with pytest.raises(ValueError, match="strictly positive"):
        gaussian_nll(_t(0.0), _t(0.0), _t(bad_scale))


def test_unknown_reduction_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown reduction"):
        gaussian_nll(_t(0.0), _t(0.0), _t(1.0), reduction="median")
