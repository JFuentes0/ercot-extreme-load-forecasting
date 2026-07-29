"""Uniform-weight equivalence validation.

Freeze section 9 item 5, described there as the load-bearing test of the design:
if uniform-weight AdaCNP does not reduce to CNP, the two arms differ in more
than the aggregation mechanism and freeze section 2 is violated.

Mechanically this follows from AdaCNP Eq. (14) with ``w_ij = 1 / n_c``:
``sum_i (1/n_c) r_i == (1/n_c) sum_i r_i``, which is CNP Eq. (2) under the mean
operator (AdaCNP Eq. 6). See MODEL_MECHANICS_NOTE_v1.md section 2.9.

Uniform weights are induced structurally by zeroing the final scoring layer, so
every score is equal and the softmax over context indices is exactly uniform for
any positive temperature.
"""

from __future__ import annotations

import torch

from ercot_forecasting.track_a.dataset import sample_episode_batch
from ercot_forecasting.track_a.train import build_adacnp, build_cnp, seeded_generator

CONTEXT_SIZE = 16
BATCH = 4

# Recorded tolerance for the equivalence check, in float32.
EQUIVALENCE_TOLERANCE = 1.0e-6


def _force_uniform_weights(model) -> None:
    """Zero the scoring head so all relevance scores are identical."""
    final = model.aggregator.scoring[-1]
    with torch.no_grad():
        final.weight.zero_()
        final.bias.zero_()


def test_uniform_weight_adacnp_reproduces_cnp(small_config, primary_seed, capsys):
    """AdaCNP under uniform weights reproduces CNP numerically."""
    cnp = build_cnp(small_config, primary_seed)
    adacnp = build_adacnp(small_config, primary_seed)

    # Isolate the aggregation mechanism: give both arms identical encoder and
    # decoder parameters, so any difference must come from aggregation alone.
    adacnp.encoder.load_state_dict(cnp.encoder.state_dict())
    adacnp.decoder.load_state_dict(cnp.decoder.state_dict())
    _force_uniform_weights(adacnp)

    pool_x = torch.randn(
        96,
        small_config["synthetic"]["feature_dim"],
        generator=seeded_generator(primary_seed),
    )
    pool_y = torch.randn(
        96, small_config["horizon"], generator=seeded_generator(primary_seed + 1)
    )
    batch = sample_episode_batch(
        pool_x=pool_x,
        pool_y=pool_y,
        batch_size=BATCH,
        context_size=CONTEXT_SIZE,
        generator=seeded_generator(primary_seed),
    )

    cnp.eval()
    adacnp.eval()
    with torch.no_grad():
        cnp_out = cnp(batch.context_x, batch.context_y, batch.target_x)
        ada_out = adacnp(batch.context_x, batch.context_y, batch.target_x)

    uniform = torch.full_like(ada_out.weights, 1.0 / CONTEXT_SIZE)
    weight_error = (ada_out.weights - uniform).abs().max().item()
    mean_error = (ada_out.mean - cnp_out.mean).abs().max().item()
    scale_error = (ada_out.scale - cnp_out.scale).abs().max().item()

    with capsys.disabled():
        print(
            f"\n[uniform-equivalence] tolerance={EQUIVALENCE_TOLERANCE:.1e} "
            f"max_abs_weight_error={weight_error:.3e} "
            f"max_abs_mean_error={mean_error:.3e} "
            f"max_abs_scale_error={scale_error:.3e}"
        )

    assert weight_error <= EQUIVALENCE_TOLERANCE
    assert mean_error <= EQUIVALENCE_TOLERANCE
    assert scale_error <= EQUIVALENCE_TOLERANCE


def test_both_arms_consume_identical_context_indices(
    small_config, primary_seed, synthetic_pool
):
    """Both arms must consume the same context set.

    Track A rules require CNP and AdaCNP to consume identical context indices,
    and freeze section 4 requires context selection to happen once per episode
    with both arms consuming the same persisted set. Selection lives in the
    dataset layer, not in either model, so one episode batch feeds both arms and
    neither can re-select or re-order.
    """
    pool_x, pool_y, _ = synthetic_pool
    first = sample_episode_batch(
        pool_x=pool_x,
        pool_y=pool_y,
        batch_size=BATCH,
        context_size=CONTEXT_SIZE,
        generator=seeded_generator(primary_seed),
    )
    second = sample_episode_batch(
        pool_x=pool_x,
        pool_y=pool_y,
        batch_size=BATCH,
        context_size=CONTEXT_SIZE,
        generator=seeded_generator(primary_seed),
    )

    assert torch.equal(first.context_indices, second.context_indices)
    assert torch.equal(first.target_indices, second.target_indices)
    assert first.context_indices.shape == (BATCH, CONTEXT_SIZE)

    # A target day never appears in its own context set.
    for row in range(BATCH):
        assert int(first.target_indices[row]) not in set(
            first.context_indices[row].tolist()
        )

    cnp = build_cnp(small_config, primary_seed)
    adacnp = build_adacnp(small_config, primary_seed)
    cnp_out = cnp(first.context_x, first.context_y, first.target_x)
    ada_out = adacnp(first.context_x, first.context_y, first.target_x)

    assert cnp_out.weights.shape == ada_out.weights.shape


def test_shared_arms_have_identical_encoder_and_decoder(small_config, primary_seed):
    """At a common seed both arms initialise encoder and decoder identically.

    This is what lets freeze section 2's controlled comparison hold in practice:
    the arms are built from one shared assembly, and the aggregator is
    constructed last so it cannot perturb the shared draws.
    """
    cnp = build_cnp(small_config, primary_seed)
    adacnp = build_adacnp(small_config, primary_seed)

    for (name, left), (other, right) in zip(
        cnp.encoder.state_dict().items(), adacnp.encoder.state_dict().items()
    ):
        assert name == other
        assert torch.equal(left, right), f"encoder parameter {name} differs"

    for (name, left), (other, right) in zip(
        cnp.decoder.state_dict().items(), adacnp.decoder.state_dict().items()
    ):
        assert name == other
        assert torch.equal(left, right), f"decoder parameter {name} differs"
