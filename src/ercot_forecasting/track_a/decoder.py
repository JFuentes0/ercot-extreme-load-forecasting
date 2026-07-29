"""Decoder g_theta.

Implements CNP Eq. (3) / AdaCNP Eqs. (7) and (15): ``phi_j = g_theta(x_j, r_j)``
with ``g_theta : X x R^{d_r} -> Phi``. The aggregated representation is
concatenated to the target input (CNP section 4.1).

Output follows freeze section 6: 24 Gaussian means and 24 positive Gaussian
scales, the scale produced by softplus plus a frozen numerical floor. Neither
reference paper specifies a positivity transform; the softplus and the floor are
the freeze's, not the papers'. See MODEL_MECHANICS_NOTE_v1.md section 4.4.

Freeze section 2 requires both arms to use an identical decoder. This module is
shared unchanged by both.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F
from torch import Tensor, nn


@dataclass(frozen=True)
class DecoderConfig:
    """Decoder shape and the frozen scale floor."""

    feature_dim: int
    representation_dim: int
    hidden_dim: int
    horizon: int
    scale_floor: float


class GaussianDecoder(nn.Module):
    """Emits per-hour Gaussian means and strictly positive scales."""

    def __init__(self, config: DecoderConfig) -> None:
        super().__init__()
        if config.scale_floor <= 0.0:
            raise ValueError(f"scale_floor must be positive, got {config.scale_floor}")
        self.config = config

        input_dim = config.feature_dim + config.representation_dim
        # Five-layer MLP, following the CNP paper's regression decoder depth.
        self.net = nn.Sequential(
            nn.Linear(input_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, 2 * config.horizon),
        )

    def forward(self, target_x: Tensor, aggregated: Tensor) -> tuple[Tensor, Tensor]:
        """Decode target distribution parameters.

        Args:
            target_x: ``(B, n_t, d_x)``
            aggregated: ``(B, n_t, d_r)``

        Returns:
            ``mean`` ``(B, n_t, horizon)`` and ``scale`` ``(B, n_t, horizon)``,
            with every scale strictly positive.
        """
        if target_x.shape[:-1] != aggregated.shape[:-1]:
            raise ValueError(
                "target_x and aggregated must agree on batch and target axes: "
                f"{tuple(target_x.shape)} vs {tuple(aggregated.shape)}"
            )
        combined = torch.cat([target_x, aggregated], dim=-1)
        raw = self.net(combined)
        mean, raw_scale = raw.chunk(2, dim=-1)
        scale = F.softplus(raw_scale) + self.config.scale_floor
        return mean, scale
