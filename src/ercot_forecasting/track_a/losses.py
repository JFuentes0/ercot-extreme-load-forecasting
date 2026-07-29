"""Training and evaluation losses.

Gaussian negative log likelihood, matching the training objective of CNP
Eq. (4) and AdaCNP Eq. (8), and the Track A primary metric (freeze section 7).

The decoder emits a positive *scale* (freeze section 6), so the scale is squared
here to obtain the variance rather than being treated as a variance directly.
See MODEL_MECHANICS_NOTE_v1.md section 4.5.
"""

from __future__ import annotations

import math

import torch
from torch import Tensor

_LOG_TWO_PI = math.log(2.0 * math.pi)


def gaussian_nll(
    target: Tensor,
    mean: Tensor,
    scale: Tensor,
    reduction: str = "mean",
) -> Tensor:
    """Gaussian negative log likelihood.

    Args:
        target: ``(B, n_t, horizon)`` observed values.
        mean: ``(B, n_t, horizon)`` predicted means.
        scale: ``(B, n_t, horizon)`` predicted standard deviations, positive.
        reduction: ``"mean"``, ``"sum"``, or ``"none"``.

    Returns:
        Scalar loss, or the elementwise tensor when ``reduction="none"``.

    Raises:
        ValueError: on shape mismatch, non-positive scale, or unknown reduction.
    """
    if not (target.shape == mean.shape == scale.shape):
        raise ValueError(
            "target, mean, and scale must share a shape: "
            f"{tuple(target.shape)}, {tuple(mean.shape)}, {tuple(scale.shape)}"
        )
    if bool(torch.any(scale <= 0.0)):
        raise ValueError("scale must be strictly positive")

    variance = scale.pow(2)
    elementwise = 0.5 * (
        _LOG_TWO_PI + torch.log(variance) + (target - mean).pow(2) / variance
    )

    if reduction == "none":
        return elementwise
    if reduction == "sum":
        return elementwise.sum()
    if reduction == "mean":
        return elementwise.mean()
    raise ValueError(f"unknown reduction {reduction!r}")
