"""Output-shape and scale-positivity validations.

Covers freeze section 9 items 1, 2, 3, and 4.
"""

from __future__ import annotations

import torch

from ercot_forecasting.track_a.dataset import sample_episode_batch
from ercot_forecasting.track_a.train import seeded_generator

BATCH = 4
TEST_CONTEXT_SIZE = 16


def _episode(pool, seed: int):
    pool_x, pool_y, _ = pool
    return sample_episode_batch(
        pool_x=pool_x,
        pool_y=pool_y,
        batch_size=BATCH,
        context_size=TEST_CONTEXT_SIZE,
        generator=seeded_generator(seed),
    )


def test_cnp_output_shapes(cnp_model, synthetic_pool, primary_seed, small_config):
    """Freeze section 9 item 3: CNP output shapes are correct."""
    batch = _episode(synthetic_pool, primary_seed)
    prediction = cnp_model(batch.context_x, batch.context_y, batch.target_x)

    horizon = small_config["horizon"]
    assert horizon == 24, "freeze section 6 fixes a 24-hour horizon"

    expected = (BATCH, batch.n_targets, horizon)
    assert prediction.mean.shape == expected
    assert prediction.scale.shape == expected
    assert prediction.weights.shape == (BATCH, batch.n_targets, TEST_CONTEXT_SIZE)
    assert torch.isfinite(prediction.mean).all()
    assert torch.isfinite(prediction.scale).all()


def test_adacnp_output_shapes(adacnp_model, synthetic_pool, primary_seed, small_config):
    """Freeze section 9 item 4: AdaCNP output shapes are correct."""
    batch = _episode(synthetic_pool, primary_seed)
    prediction = adacnp_model(batch.context_x, batch.context_y, batch.target_x)

    horizon = small_config["horizon"]
    expected = (BATCH, batch.n_targets, horizon)
    assert prediction.mean.shape == expected
    assert prediction.scale.shape == expected
    assert prediction.weights.shape == (BATCH, batch.n_targets, TEST_CONTEXT_SIZE)
    assert torch.isfinite(prediction.mean).all()
    assert torch.isfinite(prediction.scale).all()


def test_predicted_scales_are_positive(
    cnp_model, adacnp_model, synthetic_pool, primary_seed, small_config
):
    """Freeze section 9 item 2: predicted scales are strictly positive.

    The floor is a frozen constant (freeze section 6), so every scale must also
    be at least the floor.
    """
    batch = _episode(synthetic_pool, primary_seed)
    floor = float(small_config["scale_floor"])

    for model in (cnp_model, adacnp_model):
        prediction = model(batch.context_x, batch.context_y, batch.target_x)
        assert bool((prediction.scale > 0.0).all())
        assert bool((prediction.scale >= floor).all())

    # Positivity must survive an extreme input, not merely a typical one.
    hostile = batch.context_y * 1.0e4
    for model in (cnp_model, adacnp_model):
        prediction = model(batch.context_x, hostile, batch.target_x)
        assert bool((prediction.scale > 0.0).all())
        assert bool((prediction.scale >= floor).all())


def test_adaptive_weights_sum_to_one(adacnp_model, synthetic_pool, primary_seed):
    """Freeze section 9 item 1: adaptive weights sum to one."""
    batch = _episode(synthetic_pool, primary_seed)
    prediction = adacnp_model(batch.context_x, batch.context_y, batch.target_x)

    totals = prediction.weights.sum(dim=-1)
    assert torch.allclose(totals, torch.ones_like(totals), atol=1.0e-6)
    assert bool((prediction.weights >= 0.0).all())


def test_uniform_arm_weights_are_uniform(cnp_model, synthetic_pool, primary_seed):
    """The CNP arm reports genuinely uniform weights."""
    batch = _episode(synthetic_pool, primary_seed)
    prediction = cnp_model(batch.context_x, batch.context_y, batch.target_x)

    expected = torch.full_like(prediction.weights, 1.0 / TEST_CONTEXT_SIZE)
    assert torch.allclose(prediction.weights, expected, atol=1.0e-7)


def test_context_permutation_invariance(adacnp_model, synthetic_pool, primary_seed):
    """Aggregation is permutation-invariant in the context set.

    Stated for AdaCNP at paper page 5, following Eq. (15).
    """
    batch = _episode(synthetic_pool, primary_seed)
    baseline = adacnp_model(batch.context_x, batch.context_y, batch.target_x)

    order = torch.randperm(batch.context_size, generator=seeded_generator(7))
    shuffled = adacnp_model(
        batch.context_x[:, order], batch.context_y[:, order], batch.target_x
    )

    assert torch.allclose(baseline.mean, shuffled.mean, atol=1.0e-6)
    assert torch.allclose(baseline.scale, shuffled.scale, atol=1.0e-6)
