"""Aggregation mechanisms.

Freeze section 1 makes aggregation the intended and only model difference
between the two arms, so this module holds the whole of that difference:

* :class:`UniformMeanAggregator` implements CNP Eq. (2) with the mean operator,
  ``r = (1/n_c) sum_i r_i`` (AdaCNP Eq. 6).
* :class:`AdaptiveAggregator` implements AdaCNP Eqs. (9)-(14): embed inputs,
  score each (context, target) pair, normalise with a temperature-scaled
  softmax, and take the weighted sum of the *same* context representations.

Both return an explicit weight tensor so that the sum-to-one property and the
uniform-weight reduction are directly testable.

The adaptive path consumes target inputs ``x`` only. Target outcomes ``y`` are
not a parameter of any function here (freeze section 3).
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor, nn


class UniformMeanAggregator(nn.Module):
    """Uniform mean aggregation over context representations (CNP arm)."""

    def forward(
        self,
        representations: Tensor,
        context_x: Tensor,
        target_x: Tensor,
    ) -> tuple[Tensor, Tensor]:
        """Aggregate uniformly.

        ``context_x`` and ``target_x`` are accepted so both arms present the
        same call signature; the uniform mean ignores them beyond taking the
        target count.

        Args:
            representations: ``(B, n_c, d_r)``
            context_x: ``(B, n_c, d_x)``
            target_x: ``(B, n_t, d_x)``

        Returns:
            ``(B, n_t, d_r)`` aggregated representation and ``(B, n_t, n_c)``
            weights, every weight equal to ``1 / n_c``.
        """
        del context_x  # not used by uniform aggregation
        batch, n_context, _ = representations.shape
        n_targets = target_x.shape[1]

        pooled = representations.mean(dim=1, keepdim=True)
        aggregated = pooled.expand(batch, n_targets, representations.shape[-1])

        weights = representations.new_full(
            (batch, n_targets, n_context), 1.0 / n_context
        )
        return aggregated.contiguous(), weights


@dataclass(frozen=True)
class AdaptiveConfig:
    """Adaptive-layer shape.

    ``temperature`` is AdaCNP's ``tau``. The paper requires ``tau > 0`` but
    states no value; see docs/track_a/MODEL_MECHANICS_NOTE_v1.md section 9.3.
    """

    feature_dim: int
    embedding_dim: int
    scoring_hidden: int
    temperature: float


class AdaptiveAggregator(nn.Module):
    """Target-conditioned adaptive weighting (AdaCNP arm)."""

    def __init__(self, config: AdaptiveConfig) -> None:
        super().__init__()
        if config.temperature <= 0.0:
            raise ValueError(f"temperature must be positive, got {config.temperature}")
        self.config = config

        # phi_omega : X -> R^{d_e}  (AdaCNP Eq. 9). Inputs only.
        self.embedding = nn.Sequential(
            nn.Linear(config.feature_dim, config.embedding_dim),
            nn.ReLU(),
            nn.Linear(config.embedding_dim, config.embedding_dim),
        )
        # f_psi : R^{d_e} x R^{d_e} -> R  (AdaCNP Eq. 11), as a lightweight MLP
        # on the concatenated embedding pair.
        self.scoring = nn.Sequential(
            nn.Linear(2 * config.embedding_dim, config.scoring_hidden),
            nn.ReLU(),
            nn.Linear(config.scoring_hidden, 1),
        )

    def score(self, context_x: Tensor, target_x: Tensor) -> Tensor:
        """Relevance scores ``s_ij`` from inputs alone (AdaCNP Eqs. 10, 12).

        Returns:
            ``(B, n_t, n_c)`` scores.
        """
        context_embedding = self.embedding(context_x)
        target_embedding = self.embedding(target_x)

        batch, n_context, embed_dim = context_embedding.shape
        n_targets = target_embedding.shape[1]

        context_grid = context_embedding.unsqueeze(1).expand(
            batch, n_targets, n_context, embed_dim
        )
        target_grid = target_embedding.unsqueeze(2).expand(
            batch, n_targets, n_context, embed_dim
        )
        pair = torch.cat([context_grid, target_grid], dim=-1)
        return self.scoring(pair).squeeze(-1)

    def forward(
        self,
        representations: Tensor,
        context_x: Tensor,
        target_x: Tensor,
    ) -> tuple[Tensor, Tensor]:
        """Aggregate with target-conditioned weights.

        Args:
            representations: ``(B, n_c, d_r)``
            context_x: ``(B, n_c, d_x)``
            target_x: ``(B, n_t, d_x)``

        Returns:
            ``(B, n_t, d_r)`` aggregated representation and ``(B, n_t, n_c)``
            weights summing to one over the context axis.
        """
        scores = self.score(context_x, target_x)
        weights = torch.softmax(scores / self.config.temperature, dim=-1)
        aggregated = torch.matmul(weights, representations)
        return aggregated, weights
