"""Context-set construction conditions (decision **D-013**).

Track A originally built every context set by **nearest-neighbour retrieval**:
the 64 issuance-safe days closest to the target in input space. Hu et al. do
something different — Algorithm 1 line 3 and Algorithm 2 line 2 both *sample*
the context set from the historical pool, with no similarity pre-selection.

That difference is not cosmetic, and it cuts against the experiment's own
hypothesis. AdaCNP's contribution is target-conditioned reweighting of context
points; standard CNP's weakness is that uniform averaging dilutes irrelevant
context. Handing **both** arms a set of 64 already-similar days performs part of
that relevance selection in the data pipeline and gives it to the CNP baseline
for free, which compresses the very gap the experiment measures.

This module therefore provides both conditions so the comparison can be run
either way:

``NEAREST``
    The 64 issuance-safe days nearest the target in input space. Track A's
    original condition. Operationally motivated — a forecaster would look at
    similar days — and it makes CNP a deliberately strong baseline.

``SAMPLED``
    ``context_size`` days drawn uniformly at random, without replacement, from
    the issuance-safe pool, under the run's frozen seed. Faithful to Hu et al.

Both conditions:

* draw only from the fold's admissible pool, so the held-out event and its
  ±7-day buffer can never supply a context day (freeze §3);
* respect the issuance cutoff, so no candidate day extends past 09:00
  ``America/Chicago`` on D−1 (D-007);
* are persisted to disk and re-read by each arm, so the two arms provably
  consume byte-identical context indices (Track A rules);
* read target and candidate **inputs only** — outcomes never enter selection,
  so neither path can leak a target ``y``.
"""

from __future__ import annotations

from datetime import date, timedelta
from enum import Enum

import numpy as np
import torch


class ContextCondition(str, Enum):
    """How a context set is drawn from the issuance-safe pool."""

    NEAREST = "nearest"
    SAMPLED = "sampled"

    @property
    def description(self) -> str:
        if self is ContextCondition.NEAREST:
            return "nearest-in-input-space retrieval (Track A original)"
        return "uniform random sampling without replacement (Hu et al. Alg. 1/2)"


#: A candidate context day must end before the target's issuance cutoff. The
#: cutoff is 09:00 local on D-1 and a day's last hour begins at 23:00 local, so
#: the newest admissible candidate is D-2.
MIN_CONTEXT_LAG_DAYS = 2


def admissible_count(
    target_day: date, pool_days: np.ndarray, min_lag_days: int = MIN_CONTEXT_LAG_DAYS
) -> int:
    """How many pool days precede the target's issuance cutoff.

    ``pool_days`` must be ascending; the caller owns that invariant and
    :func:`sample_context_indices` asserts it.
    """
    latest = target_day - timedelta(days=min_lag_days)
    return int(np.searchsorted(pool_days, latest, side="right"))


def sample_context_indices(
    target_days: tuple[date, ...],
    pool_days: tuple[date, ...],
    context_size: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Draw context sets uniformly at random from the issuance-safe pool.

    The paper-faithful condition. For each target, the candidate set is every
    pool day at or before the issuance cutoff; ``context_size`` of them are
    drawn without replacement. Targets with too few candidates are dropped
    rather than padded — padding would either repeat a day or reach past the
    cutoff.

    Selection consumes **no** target or candidate outcome, only the day
    identities, so it is structurally incapable of leaking a target ``y``.

    Returns the selected indices and the positions of the surviving targets in
    ``target_days``.
    """
    pool_array = np.array(pool_days)
    if not np.all(pool_array[:-1] <= pool_array[1:]):
        raise ValueError("pool_days must be ascending for the issuance-safe bound")

    generator = np.random.default_rng(seed)
    rows: list[np.ndarray] = []
    kept: list[int] = []

    for position, target_day in enumerate(target_days):
        admissible = admissible_count(target_day, pool_array)
        if admissible < context_size:
            continue
        rows.append(
            np.sort(generator.choice(admissible, size=context_size, replace=False))
        )
        kept.append(position)

    if not kept:
        raise ValueError("no target had enough issuance-safe context candidates")
    return np.vstack(rows), np.array(kept, dtype=np.int64)


def nearest_context_indices(
    target_days: tuple[date, ...],
    target_x: torch.Tensor,
    pool_days: tuple[date, ...],
    pool_x: torch.Tensor,
    context_size: int,
    chunk: int = 256,
) -> tuple[np.ndarray, np.ndarray]:
    """Nearest-in-input-space context, restricted to issuance-safe candidates.

    Delegates to the existing stage-3 implementation so the two conditions share
    one definition of the issuance bound rather than two that must be kept in
    step.
    """
    from ercot_forecasting.track_a.stage3 import select_context_indices

    return select_context_indices(
        target_days=target_days,
        target_x=target_x,
        pool_days=pool_days,
        pool_x=pool_x,
        context_size=context_size,
        chunk=chunk,
    )


def build_context_indices(
    condition: ContextCondition,
    target_days: tuple[date, ...],
    target_x: torch.Tensor,
    pool_days: tuple[date, ...],
    pool_x: torch.Tensor,
    context_size: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Dispatch to the configured context condition."""
    if condition is ContextCondition.SAMPLED:
        return sample_context_indices(target_days, pool_days, context_size, seed)
    return nearest_context_indices(
        target_days, target_x, pool_days, pool_x, context_size
    )
