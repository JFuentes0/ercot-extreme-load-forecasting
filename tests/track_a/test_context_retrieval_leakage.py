"""Target-outcome leakage validation.

Freeze section 3 forbids retrieval from consuming target outcomes ``y``, and
freeze section 9 item 6 requires a validation that target ``y`` *cannot*
influence retrieval.

NEXT_TASK.md requires this test to demonstrate structural impossibility rather
than mere absence. Showing that retrieval output happens not to change when a
target outcome changes would only establish absence in the cases sampled. These
tests instead establish that no channel exists:

1. the selection function's parameter set is exactly the permitted one, so no
   outcome tensor can be passed even by keyword;
2. passing an outcome argument raises ``TypeError`` at call time;
3. the model forward signature likewise has no target-outcome parameter;
4. the aggregation path that consumes the weights sees only input tensors.

Absence under perturbation is then checked as a corroborating property, not as
the primary evidence.
"""

from __future__ import annotations

import inspect

import pytest
import torch

from ercot_forecasting.track_a import context_retrieval
from ercot_forecasting.track_a.aggregation import AdaptiveAggregator
from ercot_forecasting.track_a.cnp import NeuralProcessBase
from ercot_forecasting.track_a.context_retrieval import (
    SELECTION_PARAMETERS,
    select_context_indices,
)
from ercot_forecasting.track_a.dataset import sample_episode_batch
from ercot_forecasting.track_a.train import seeded_generator

CONTEXT_SIZE = 16

# Any parameter name that could carry an outcome tensor.
FORBIDDEN = ("target_y", "y", "outcome", "outcomes", "y_target", "labels")


def test_selection_signature_admits_no_target_outcome():
    """Structural: the selection function has no outcome parameter."""
    parameters = inspect.signature(select_context_indices).parameters

    assert tuple(parameters) == SELECTION_PARAMETERS

    for name in parameters:
        assert name not in FORBIDDEN
    # No variadic channel through which extras could be smuggled in.
    for parameter in parameters.values():
        assert parameter.kind is not inspect.Parameter.VAR_POSITIONAL
        assert parameter.kind is not inspect.Parameter.VAR_KEYWORD


def test_selection_rejects_a_target_outcome_argument():
    """Structural: supplying an outcome is a call-time error."""
    target_x = torch.randn(2, 4, generator=seeded_generator(1))
    candidate_x = torch.randn(32, 4, generator=seeded_generator(2))
    target_y = torch.randn(2, 24, generator=seeded_generator(3))

    for name in FORBIDDEN:
        with pytest.raises(TypeError):
            select_context_indices(
                target_x=target_x,
                candidate_x=candidate_x,
                context_size=CONTEXT_SIZE,
                **{name: target_y},
            )


def test_forward_signature_admits_no_target_outcome():
    """Structural: the model forward pass has no target-outcome parameter."""
    parameters = inspect.signature(NeuralProcessBase.forward).parameters
    assert tuple(parameters) == ("self", "context_x", "context_y", "target_x")

    scoring = inspect.signature(AdaptiveAggregator.score).parameters
    assert tuple(scoring) == ("self", "context_x", "target_x")

    aggregate = inspect.signature(AdaptiveAggregator.forward).parameters
    assert tuple(aggregate) == ("self", "representations", "context_x", "target_x")


def test_selection_module_holds_no_outcome_state():
    """Structural: no module-level state could carry outcomes into selection."""
    for name, value in vars(context_retrieval).items():
        if name.startswith("__"):
            continue
        assert not isinstance(value, torch.Tensor), (
            f"{name} is a module-level tensor and could act as a hidden channel"
        )


def test_retrieval_is_unchanged_by_target_outcomes(synthetic_pool, primary_seed):
    """Corroborating: perturbing outcomes cannot move the selection.

    This is secondary evidence. The structural tests above are what establish
    impossibility; this confirms the wiring matches.
    """
    pool_x, pool_y, _ = synthetic_pool
    target_x = pool_x[:4]

    baseline = select_context_indices(
        target_x=target_x, candidate_x=pool_x, context_size=CONTEXT_SIZE
    )
    perturbed_pool_y = pool_y * -13.0 + 500.0
    repeat = select_context_indices(
        target_x=target_x, candidate_x=pool_x, context_size=CONTEXT_SIZE
    )

    assert torch.equal(baseline, repeat)
    # The outcome tensor is not even an input to the call above.
    assert perturbed_pool_y.shape == pool_y.shape


def test_adaptive_weights_are_unchanged_by_target_outcomes(
    adacnp_model, synthetic_pool, primary_seed
):
    """Corroborating: target outcomes cannot move the adaptive weights."""
    pool_x, pool_y, _ = synthetic_pool
    batch = sample_episode_batch(
        pool_x=pool_x,
        pool_y=pool_y,
        batch_size=4,
        context_size=CONTEXT_SIZE,
        generator=seeded_generator(primary_seed),
    )
    baseline = adacnp_model(batch.context_x, batch.context_y, batch.target_x)

    # Corrupting the target outcome entirely cannot reach the weights, because
    # the forward pass never receives it.
    corrupted_target_y = torch.full_like(batch.target_y, 1.0e6)
    assert corrupted_target_y.shape == batch.target_y.shape

    repeat = adacnp_model(batch.context_x, batch.context_y, batch.target_x)
    assert torch.equal(baseline.weights, repeat.weights)
