"""Synthetic episode construction for the Track A scaffold.

Synthetic fixtures only. Nothing in this module reads a file, and no real
ERCOT, EIA, weather, event, or censoring artifact is referenced.

Episode structure follows freeze section 3: one episode targets one target day
and the target output is a 24-hour vector. The generated pool carries a regime
split (normal and extreme) so the scaffold exercises the shifted-regime case the
Track A comparison is about, without standing in for any real event inventory.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor

from ercot_forecasting.track_a.context_retrieval import (
    gather_context,
    select_context_indices,
)


@dataclass(frozen=True)
class SyntheticPoolConfig:
    """Shape of a generated synthetic pool.

    These are fixture dimensions. They are not event counts, fold counts, or
    inventory sizes (decision D-006, freeze section 10.1).
    """

    pool_days: int
    feature_dim: int
    horizon: int
    extreme_fraction: float = 0.25


@dataclass(frozen=True)
class EpisodeBatch:
    """A batch of episodes.

    Attributes:
        context_x: ``(B, n_c, d_x)``
        context_y: ``(B, n_c, horizon)``
        target_x: ``(B, n_t, d_x)``
        target_y: ``(B, n_t, horizon)``
        context_indices: ``(B, n_c)`` pool indices of the selected context.
        target_indices: ``(B,)`` pool indices of the target days.

    ``context_indices`` is retained so the context set behind every prediction
    is recoverable, and so both arms can be shown to have consumed the same
    context (Track A rules: identical context indices for both arms; save
    context IDs for every prediction).
    """

    context_x: Tensor
    context_y: Tensor
    target_x: Tensor
    target_y: Tensor
    context_indices: Tensor
    target_indices: Tensor

    @property
    def batch_size(self) -> int:
        return self.context_x.shape[0]

    @property
    def context_size(self) -> int:
        return self.context_x.shape[1]

    @property
    def n_targets(self) -> int:
        return self.target_x.shape[1]

    @property
    def horizon(self) -> int:
        return self.target_y.shape[-1]


def make_synthetic_pool(
    config: SyntheticPoolConfig,
    generator: torch.Generator,
) -> tuple[Tensor, Tensor, Tensor]:
    """Generate a synthetic pool of days.

    Each day carries a feature vector and a 24-hour curve. A regime indicator
    marks a minority of days as extreme; those days follow a different
    input-output mapping, mirroring the phase-transition structure the AdaCNP
    paper uses in its 1-D study while remaining entirely synthetic.

    Returns:
        ``pool_x`` ``(pool_days, d_x)``, ``pool_y`` ``(pool_days, horizon)``,
        and a boolean ``is_extreme`` ``(pool_days,)``.
    """
    n = config.pool_days
    d_x = config.feature_dim
    horizon = config.horizon

    pool_x = torch.randn(n, d_x, generator=generator)

    # Regime assignment is a deterministic function of a generated score, so a
    # given seed always produces the same split.
    score = torch.randn(n, generator=generator)
    threshold = torch.quantile(score, 1.0 - config.extreme_fraction)
    is_extreme = score > threshold

    hours = torch.arange(horizon, dtype=torch.float32)
    daily_shape = torch.sin(2.0 * torch.pi * hours / horizon)

    weights_normal = torch.randn(d_x, generator=generator)
    weights_extreme = torch.randn(d_x, generator=generator)

    level_normal = pool_x @ weights_normal
    level_extreme = pool_x @ weights_extreme

    level = torch.where(is_extreme, level_extreme * 2.0 + 3.0, level_normal)
    amplitude = torch.where(
        is_extreme, torch.full_like(level, 1.8), torch.ones_like(level)
    )

    noise_scale = torch.where(is_extreme, 0.30, 0.10)
    noise = torch.randn(n, horizon, generator=generator) * noise_scale.unsqueeze(1)

    pool_y = (
        level.unsqueeze(1) + amplitude.unsqueeze(1) * daily_shape.unsqueeze(0) + noise
    )
    return pool_x, pool_y, is_extreme


def build_episodes(
    pool_x: Tensor,
    pool_y: Tensor,
    target_indices: Tensor,
    context_size: int,
    n_targets: int = 1,
) -> EpisodeBatch:
    """Build episodes for the given target days.

    Context selection consumes target inputs only, via
    :func:`select_context_indices`. A target day is never eligible as its own
    context.

    Args:
        pool_x: ``(pool_days, d_x)``
        pool_y: ``(pool_days, horizon)``
        target_indices: ``(B,)`` indices of target days.
        context_size: context items per target.
        n_targets: targets per episode. Freeze section 3 gives one target day
            per episode; the axis is retained so the general path is exercised.
    """
    if target_indices.ndim != 1:
        raise ValueError(
            f"target_indices must be 1-D, got shape {tuple(target_indices.shape)}"
        )

    batch = target_indices.shape[0]
    pool_days = pool_x.shape[0]

    target_x = pool_x[target_indices].unsqueeze(1).expand(batch, n_targets, -1)
    target_y = pool_y[target_indices].unsqueeze(1).expand(batch, n_targets, -1)

    flat_target_x = target_x.reshape(batch * n_targets, -1)

    # A target day may not serve as its own context.
    excluded = torch.zeros(batch * n_targets, pool_days, dtype=torch.bool)
    repeated = target_indices.repeat_interleave(n_targets)
    excluded[torch.arange(batch * n_targets), repeated] = True

    indices = select_context_indices(
        target_x=flat_target_x,
        candidate_x=pool_x,
        context_size=context_size,
        excluded=excluded,
    )
    context_x, context_y = gather_context(pool_x, pool_y, indices)

    d_x = pool_x.shape[1]
    horizon = pool_y.shape[1]

    # Collapse the target axis into the batch for selection, then restore it.
    # One shared context set per episode: targets in an episode see the same
    # context, as required when an episode has a single target day.
    context_x = context_x.reshape(batch, n_targets, context_size, d_x)[:, 0]
    context_y = context_y.reshape(batch, n_targets, context_size, horizon)[:, 0]
    context_indices = indices.reshape(batch, n_targets, context_size)[:, 0]

    return EpisodeBatch(
        context_x=context_x.contiguous(),
        context_y=context_y.contiguous(),
        target_x=target_x.contiguous(),
        target_y=target_y.contiguous(),
        context_indices=context_indices.contiguous(),
        target_indices=target_indices.clone(),
    )


def sample_episode_batch(
    pool_x: Tensor,
    pool_y: Tensor,
    batch_size: int,
    context_size: int,
    generator: torch.Generator,
    n_targets: int = 1,
) -> EpisodeBatch:
    """Sample a batch of episodes with randomly chosen target days."""
    target_indices = torch.randint(
        low=0,
        high=pool_x.shape[0],
        size=(batch_size,),
        generator=generator,
    )
    return build_episodes(
        pool_x=pool_x,
        pool_y=pool_y,
        target_indices=target_indices,
        context_size=context_size,
        n_targets=n_targets,
    )
