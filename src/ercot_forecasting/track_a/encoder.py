"""Context encoder h_theta.

Implements CNP Eq. (1) / AdaCNP Eq. (5): each context pair is mapped
independently to a representation vector, ``r_i = h_theta(x_i, y_i)``, with
``h_theta : X x Y -> R^{d_r}``.

Freeze section 2 requires both arms to use an identical encoder. This module is
shared unchanged by both.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor, nn


@dataclass(frozen=True)
class EncoderConfig:
    """Encoder shape.

    Depth follows the three-layer MLP encoder reported in the CNP paper
    section 4.1; widths are engineering defaults. See
    docs/track_a/MODEL_MECHANICS_NOTE_v1.md section 9.6.
    """

    feature_dim: int
    horizon: int
    hidden_dim: int
    representation_dim: int


class ContextEncoder(nn.Module):
    """Maps each ``(x_i, y_i)`` context pair to ``r_i``."""

    def __init__(self, config: EncoderConfig) -> None:
        super().__init__()
        self.config = config
        input_dim = config.feature_dim + config.horizon
        self.net = nn.Sequential(
            nn.Linear(input_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.representation_dim),
        )

    def forward(self, context_x: Tensor, context_y: Tensor) -> Tensor:
        """Encode a context set.

        Args:
            context_x: ``(B, n_c, d_x)``
            context_y: ``(B, n_c, horizon)``

        Returns:
            ``(B, n_c, d_r)`` context representations.
        """
        if context_x.shape[:-1] != context_y.shape[:-1]:
            raise ValueError(
                "context_x and context_y must agree on batch and context axes: "
                f"{tuple(context_x.shape)} vs {tuple(context_y.shape)}"
            )
        pair = torch.cat([context_x, context_y], dim=-1)
        return self.net(pair)
