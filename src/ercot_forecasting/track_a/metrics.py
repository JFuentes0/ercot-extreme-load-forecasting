"""Freeze §7 secondary metrics.

Freeze §7 requires eight secondary metrics "reported for interpretation", and
states that they **do not adjudicate the comparison** — the primary metric alone
does that (`losses.gaussian_nll`). Until now none of the eight was computed.

Definitions are pre-registered in `docs/track_a/ANALYSIS_PLAN_v1.md`, because
several of them involve a choice (which quantile bounds "high load", what counts
as a "cold" context day) and choosing after seeing results would be a
garden-of-forking-paths.

Everything here is closed-form or elementary. Nothing here is a decision rule;
these are descriptive quantities only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.special import ndtr

#: Nominal central-interval level for the calibration metric (freeze §7).
COVERAGE_LEVEL = 0.90

#: z for a two-sided 90% central interval.
COVERAGE_Z = 1.6448536269514722

#: Load quantile above which an hour counts as "high load", for the exceedance
#: metric. Taken on the fold's own training partition, never on held-out data.
HIGH_LOAD_QUANTILE = 0.99

#: A context day is "cold" if its cutoff `roll24` falls below this quantile of
#: the fold's training pool. Derived per fold; never an absolute temperature.
COLD_CONTEXT_QUANTILE = 0.10

_INV_SQRT_PI = 1.0 / math.sqrt(math.pi)


def _standard_normal_cdf(z: np.ndarray) -> np.ndarray:
    """Φ(z). `ndtr` is the vectorised C implementation — a `np.vectorize` wrapper
    around `math.erf` would be a Python loop over every scored hour."""
    return ndtr(np.asarray(z, dtype=np.float64))


def _standard_normal_pdf(z: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def gaussian_crps(
    target: np.ndarray, mean: np.ndarray, scale: np.ndarray
) -> np.ndarray:
    """Continuous ranked probability score for a Gaussian, elementwise.

    Closed form:

        CRPS(N(mu, sigma), y) = sigma * [ z(2Φ(z) − 1) + 2φ(z) − 1/sqrt(pi) ]

    with ``z = (y − mu) / sigma``. Lower is better, and unlike NLL it is bounded
    below by zero and finite for any prediction, which is why it is a useful
    companion to a likelihood that can be dominated by a single bad hour.
    """
    z = (target - mean) / scale
    return scale * (
        z * (2.0 * _standard_normal_cdf(z) - 1.0)
        + 2.0 * _standard_normal_pdf(z)
        - _INV_SQRT_PI
    )


def interval_width(scale: np.ndarray, level: float = COVERAGE_LEVEL) -> np.ndarray:
    """Width of the central predictive interval at ``level``."""
    if level != COVERAGE_LEVEL:
        raise ValueError("only the frozen 90% level is supported")
    return 2.0 * COVERAGE_Z * scale


def interval_covers(
    target: np.ndarray,
    mean: np.ndarray,
    scale: np.ndarray,
    level: float = COVERAGE_LEVEL,
) -> np.ndarray:
    """Boolean mask: does the central ``level`` interval contain the target?"""
    if level != COVERAGE_LEVEL:
        raise ValueError("only the frozen 90% level is supported")
    half = COVERAGE_Z * scale
    return (target >= mean - half) & (target <= mean + half)


def exceedance_probability(
    threshold: float, mean: np.ndarray, scale: np.ndarray
) -> np.ndarray:
    """Predicted P(Y > threshold) under the Gaussian, elementwise."""
    return 1.0 - _standard_normal_cdf((threshold - mean) / scale)


def weight_entropy(weights: np.ndarray) -> np.ndarray:
    """Shannon entropy (nats) of each row of context weights.

    Uniform weights over ``n`` contexts give ``log n``, the maximum. A fully
    concentrated weighting gives 0. CNP is uniform by construction, so its
    entropy is a useful invariant check rather than a finding.
    """
    safe = np.clip(weights, 1e-12, None)
    return -np.sum(weights * np.log(safe), axis=-1)


def effective_context_count(weights: np.ndarray) -> np.ndarray:
    """exp(entropy) — the number of contexts the weighting effectively uses.

    Equals the context size exactly under uniform weighting, so it reads on the
    same scale as the context set and is directly comparable between arms.
    """
    return np.exp(weight_entropy(weights))


def cold_context_weight(weights: np.ndarray, is_cold: np.ndarray) -> np.ndarray:
    """Share of each row's weight placed on cold context days.

    The freeze §7 metric "weight assigned to cold-context days" — the most
    direct evidence available on whether AdaCNP's mechanism does what the paper
    claims, namely concentrate on relevant extreme analogues. **Only computable
    since D-012 supplied temperature**; before that no variable identified a
    cold day.

    Under uniform weighting this equals the cold fraction of the context set, so
    the informative quantity is AdaCNP's value *relative to* CNP's.
    """
    if weights.shape != is_cold.shape:
        raise ValueError(
            f"weights {weights.shape} and is_cold {is_cold.shape} must match"
        )
    return np.sum(weights * is_cold, axis=-1)


@dataclass(frozen=True)
class SecondaryMetrics:
    """The eight freeze §7 secondary metrics for one run.

    Computed over the same scored hours as the primary metric — i.e. with
    `verified_shed` hours excluded per D-010 — so they describe the same
    estimand. ``coverage_deviation`` is freeze §7's "key calibration metric".

    The three AdaCNP-internal quantities are ``None`` where they do not apply:
    ``cold_context_weight`` needs temperature features (D-012), and all three
    need a weighted aggregator.
    """

    crps: float
    rmse: float
    mae: float
    interval_width: float
    coverage: float
    coverage_deviation: float
    high_load_threshold: float
    observed_exceedance: float
    predicted_exceedance: float
    weight_entropy: float | None
    effective_context_count: float | None
    cold_context_weight: float | None

    def as_dict(self) -> dict[str, float | None]:
        return {
            "crps": self.crps,
            "rmse": self.rmse,
            "mae": self.mae,
            "interval_width_90": self.interval_width,
            "empirical_coverage_90": self.coverage,
            "coverage_deviation_abs": self.coverage_deviation,
            "high_load_threshold_normalized": self.high_load_threshold,
            "observed_high_load_exceedance": self.observed_exceedance,
            "predicted_high_load_exceedance": self.predicted_exceedance,
            "adacnp_weight_entropy_nats": self.weight_entropy,
            "effective_context_count": self.effective_context_count,
            "cold_context_weight_share": self.cold_context_weight,
        }


def summarize(
    target: np.ndarray,
    mean: np.ndarray,
    scale: np.ndarray,
    high_load_threshold: float,
    weights: np.ndarray | None = None,
    cold_mask: np.ndarray | None = None,
) -> SecondaryMetrics:
    """Reduce elementwise predictions to the freeze §7 secondary metrics.

    ``target``, ``mean`` and ``scale`` are the *scored* hours only. ``weights``
    and ``cold_mask``, if given, are per-episode context weightings.
    """
    error = target - mean
    covered = interval_covers(target, mean, scale)
    coverage = float(np.mean(covered))

    entropy = ecc = cold = None
    if weights is not None and weights.size:
        entropy = float(np.mean(weight_entropy(weights)))
        ecc = float(np.mean(effective_context_count(weights)))
        if cold_mask is not None and cold_mask.size:
            cold = float(np.mean(cold_context_weight(weights, cold_mask)))

    return SecondaryMetrics(
        crps=float(np.mean(gaussian_crps(target, mean, scale))),
        rmse=float(np.sqrt(np.mean(error**2))),
        mae=float(np.mean(np.abs(error))),
        interval_width=float(np.mean(interval_width(scale))),
        coverage=coverage,
        coverage_deviation=abs(coverage - COVERAGE_LEVEL),
        high_load_threshold=float(high_load_threshold),
        observed_exceedance=float(np.mean(target > high_load_threshold)),
        predicted_exceedance=float(
            np.mean(exceedance_probability(high_load_threshold, mean, scale))
        ),
        weight_entropy=entropy,
        effective_context_count=ecc,
        cold_context_weight=cold,
    )
