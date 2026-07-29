"""Context retrieval for Track A episodes.

Freeze section 3 permits retrieval to consume target inputs ``x`` and forbids it
from ever consuming target outcomes ``y``. Freeze section 9 item 6 requires a
validation that target ``y`` *cannot* influence retrieval.

That requirement is met structurally rather than by convention: the selection
function in this module accepts only input tensors. There is no parameter,
attribute, or module-level state through which a target outcome could be
supplied, so no call site can pass one even by mistake. Gathering the selected
context outcomes is a separate step that operates on indices alone and performs
no selection.

See docs/track_a/MODEL_MECHANICS_NOTE_v1.md section 6.
"""

from __future__ import annotations

import torch
from torch import Tensor

# The exact parameter set of ``select_context_indices``. The leakage test asserts
# against this tuple, so widening it is a deliberate, visible change.
SELECTION_PARAMETERS: tuple[str, ...] = (
    "target_x",
    "candidate_x",
    "context_size",
    "excluded",
)


def select_context_indices(
    target_x: Tensor,
    candidate_x: Tensor,
    context_size: int,
    excluded: Tensor | None = None,
) -> Tensor:
    """Select context indices for each target from input features alone.

    Args:
        target_x: ``(n_t, d_x)`` target inputs.
        candidate_x: ``(n_pool, d_x)`` candidate-pool inputs.
        context_size: number of context items to select per target.
        excluded: optional ``(n_t, n_pool)`` boolean mask. ``True`` marks a
            candidate as ineligible for that target. This is the hook through
            which held-out-event and buffer exclusions are applied at the
            real-data stages; it carries eligibility, never outcomes.

    Returns:
        ``(n_t, context_size)`` long tensor of indices into the candidate pool.

    Raises:
        ValueError: if shapes are inconsistent or too few candidates remain.
    """
    if target_x.ndim != 2:
        raise ValueError(f"target_x must be 2-D, got shape {tuple(target_x.shape)}")
    if candidate_x.ndim != 2:
        raise ValueError(
            f"candidate_x must be 2-D, got shape {tuple(candidate_x.shape)}"
        )
    if target_x.shape[1] != candidate_x.shape[1]:
        raise ValueError(
            "target_x and candidate_x must share a feature dimension: "
            f"{target_x.shape[1]} != {candidate_x.shape[1]}"
        )
    if context_size <= 0:
        raise ValueError(f"context_size must be positive, got {context_size}")

    n_targets = target_x.shape[0]
    n_pool = candidate_x.shape[0]

    # Squared euclidean distance in input space only.
    distance = torch.cdist(target_x, candidate_x, p=2.0)

    if excluded is not None:
        if excluded.shape != (n_targets, n_pool):
            raise ValueError(
                "excluded must have shape (n_targets, n_pool), got "
                f"{tuple(excluded.shape)}"
            )
        eligible = (~excluded).sum(dim=1)
        if int(eligible.min()) < context_size:
            raise ValueError(
                "not enough eligible candidates for the requested context size"
            )
        distance = distance.masked_fill(excluded, float("inf"))
    elif n_pool < context_size:
        raise ValueError(
            f"candidate pool of {n_pool} is smaller than context size {context_size}"
        )

    # Ascending distance; ties resolved by index order, so selection is
    # deterministic for a given input pool.
    return torch.topk(distance, k=context_size, dim=1, largest=False).indices


def gather_context(
    pool_x: Tensor,
    pool_y: Tensor,
    indices: Tensor,
) -> tuple[Tensor, Tensor]:
    """Gather context pairs for previously selected indices.

    This performs no selection. It is a pure lookup, kept separate from
    :func:`select_context_indices` so that outcome tensors are touched only
    after selection has already been decided from inputs.

    Args:
        pool_x: ``(n_pool, d_x)`` candidate-pool inputs.
        pool_y: ``(n_pool, horizon)`` candidate-pool outcomes.
        indices: ``(n_t, context_size)`` indices from selection.

    Returns:
        ``(n_t, context_size, d_x)`` inputs and ``(n_t, context_size, horizon)``
        outcomes.
    """
    if indices.ndim != 2:
        raise ValueError(f"indices must be 2-D, got shape {tuple(indices.shape)}")
    if pool_x.shape[0] != pool_y.shape[0]:
        raise ValueError(
            "pool_x and pool_y must describe the same candidates: "
            f"{pool_x.shape[0]} != {pool_y.shape[0]}"
        )
    return pool_x[indices], pool_y[indices]
