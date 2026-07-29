"""Determinism and tiny-overfit validations.

Covers freeze section 9 items 7 and 8, and freeze execution stage 2 (synthetic
CPU smoke training). Synthetic fixtures only; CPU only.
"""

from __future__ import annotations

import torch

from ercot_forecasting.track_a.train import (
    build_adacnp,
    build_cnp,
    build_synthetic_pool,
    overfit_single_episode,
    smoke_train,
)

CONTEXT_SIZE = 16
SMOKE_STEPS = 30
SMOKE_BATCH = 4
OVERFIT_STEPS = 400
LEARNING_RATE = 1.0e-3


def _pool(small_config, seed):
    return build_synthetic_pool(small_config, seed)


def test_fixed_seed_reproduces_smoke_result(small_config, primary_seed):
    """Freeze section 9 item 7: a fixed seed reproduces the same smoke result."""
    pool_x, pool_y, _ = _pool(small_config, primary_seed)

    traces = []
    for _ in range(2):
        model = build_cnp(small_config, primary_seed)
        result = smoke_train(
            model=model,
            pool_x=pool_x,
            pool_y=pool_y,
            seed=primary_seed,
            steps=SMOKE_STEPS,
            batch_size=SMOKE_BATCH,
            context_size=CONTEXT_SIZE,
            learning_rate=LEARNING_RATE,
        )
        traces.append(result.losses)

    assert traces[0] == traces[1], "two runs at the same seed diverged"


def test_fixed_seed_reproduces_adacnp_smoke_result(small_config, primary_seed):
    """The determinism guarantee must hold for the adaptive arm too."""
    pool_x, pool_y, _ = _pool(small_config, primary_seed)

    traces = []
    for _ in range(2):
        model = build_adacnp(small_config, primary_seed)
        result = smoke_train(
            model=model,
            pool_x=pool_x,
            pool_y=pool_y,
            seed=primary_seed,
            steps=SMOKE_STEPS,
            batch_size=SMOKE_BATCH,
            context_size=CONTEXT_SIZE,
            learning_rate=LEARNING_RATE,
        )
        traces.append(result.losses)

    assert traces[0] == traces[1], "two AdaCNP runs at the same seed diverged"


def test_different_seeds_give_different_results(small_config, scaffold_config):
    """A determinism test is only meaningful if the seed actually matters."""
    first, second = int(scaffold_config["seeds"][0]), int(scaffold_config["seeds"][1])
    pool_x, pool_y, _ = _pool(small_config, first)

    traces = []
    for seed in (first, second):
        model = build_cnp(small_config, seed)
        result = smoke_train(
            model=model,
            pool_x=pool_x,
            pool_y=pool_y,
            seed=seed,
            steps=SMOKE_STEPS,
            batch_size=SMOKE_BATCH,
            context_size=CONTEXT_SIZE,
            learning_rate=LEARNING_RATE,
        )
        traces.append(result.losses)

    assert traces[0] != traces[1]


def test_cnp_overfits_tiny_synthetic_fixture(small_config, primary_seed):
    """Freeze section 9 item 8: the CNP arm can overfit a tiny fixture."""
    pool_x, pool_y, _ = _pool(small_config, primary_seed)
    model = build_cnp(small_config, primary_seed)

    result = overfit_single_episode(
        model=model,
        pool_x=pool_x,
        pool_y=pool_y,
        seed=primary_seed,
        steps=OVERFIT_STEPS,
        context_size=CONTEXT_SIZE,
        learning_rate=LEARNING_RATE,
    )

    assert result.final_loss < result.initial_loss
    assert torch.isfinite(torch.tensor(result.final_loss))


def test_adacnp_overfits_tiny_synthetic_fixture(small_config, primary_seed):
    """Freeze section 9 item 8: the AdaCNP arm can overfit a tiny fixture."""
    pool_x, pool_y, _ = _pool(small_config, primary_seed)
    model = build_adacnp(small_config, primary_seed)

    result = overfit_single_episode(
        model=model,
        pool_x=pool_x,
        pool_y=pool_y,
        seed=primary_seed,
        steps=OVERFIT_STEPS,
        context_size=CONTEXT_SIZE,
        learning_rate=LEARNING_RATE,
    )

    assert result.final_loss < result.initial_loss
    assert torch.isfinite(torch.tensor(result.final_loss))


def test_smoke_training_reduces_loss_for_both_arms(small_config, primary_seed):
    """Freeze execution stage 2: synthetic CPU smoke training runs and learns."""
    pool_x, pool_y, _ = _pool(small_config, primary_seed)

    for builder in (build_cnp, build_adacnp):
        model = builder(small_config, primary_seed)
        result = smoke_train(
            model=model,
            pool_x=pool_x,
            pool_y=pool_y,
            seed=primary_seed,
            steps=SMOKE_STEPS * 4,
            batch_size=SMOKE_BATCH,
            context_size=CONTEXT_SIZE,
            learning_rate=LEARNING_RATE,
        )
        assert result.final_loss < result.initial_loss
