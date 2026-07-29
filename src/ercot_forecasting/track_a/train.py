"""Synthetic CPU smoke training for the Track A scaffold.

Freeze section 10 authorises execution stages 1 (synthetic unit tests) and 2
(synthetic CPU smoke training) only. Nothing here reads a real artifact,
constructs a real partition, or produces a held-out-event result.

All training runs on CPU. Determinism is established by seeding a local
generator and the global torch RNG from a single seed, so two runs at the same
seed produce identical results.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
import yaml
from torch import nn

from ercot_forecasting.track_a.adacnp import (
    AdaptiveConditionalNeuralProcess,
    AdaptiveModelConfig,
)
from ercot_forecasting.track_a.cnp import ConditionalNeuralProcess, ModelConfig
from ercot_forecasting.track_a.dataset import (
    SyntheticPoolConfig,
    make_synthetic_pool,
    sample_episode_batch,
)
from ercot_forecasting.track_a.losses import gaussian_nll

CPU = torch.device("cpu")


def load_scaffold_config(path: str | Path) -> dict[str, Any]:
    """Load the scaffold configuration.

    The only file this module reads is its own configuration. It contains no
    real data and no reference to any real artifact.
    """
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_model_config(config: dict[str, Any]) -> ModelConfig:
    """Assemble the architecture shared by both arms (freeze section 2)."""
    return ModelConfig(
        feature_dim=config["synthetic"]["feature_dim"],
        horizon=config["horizon"],
        representation_dim=config["representation_dim"],
        encoder_hidden=config["encoder_hidden"],
        decoder_hidden=config["decoder_hidden"],
        scale_floor=float(config["scale_floor"]),
    )


def build_adaptive_config(config: dict[str, Any]) -> AdaptiveModelConfig:
    """Assemble the AdaCNP architecture from the same shared architecture."""
    return AdaptiveModelConfig(
        shared=build_model_config(config),
        embedding_dim=config["embedding_dim"],
        scoring_hidden=config["scoring_hidden"],
        temperature=float(config["temperature"]),
    )


def seeded_generator(seed: int) -> torch.Generator:
    """Return a CPU generator seeded deterministically."""
    generator = torch.Generator(device=CPU)
    generator.manual_seed(seed)
    return generator


def build_cnp(config: dict[str, Any], seed: int) -> ConditionalNeuralProcess:
    """Construct the CNP arm under a fixed seed."""
    torch.manual_seed(seed)
    return ConditionalNeuralProcess(build_model_config(config)).to(CPU)


def build_adacnp(config: dict[str, Any], seed: int) -> AdaptiveConditionalNeuralProcess:
    """Construct the AdaCNP arm under a fixed seed.

    Because the shared assembly builds encoder and decoder before the
    aggregator, this draws the same encoder and decoder initialisation as
    :func:`build_cnp` at the same seed.
    """
    torch.manual_seed(seed)
    return AdaptiveConditionalNeuralProcess(build_adaptive_config(config)).to(CPU)


@dataclass(frozen=True)
class SmokeResult:
    """Outcome of a synthetic smoke-training run."""

    losses: list[float]
    initial_loss: float
    final_loss: float

    @property
    def steps(self) -> int:
        return len(self.losses)


def smoke_train(
    model: nn.Module,
    pool_x: torch.Tensor,
    pool_y: torch.Tensor,
    seed: int,
    steps: int,
    batch_size: int,
    context_size: int,
    learning_rate: float,
) -> SmokeResult:
    """Run a short synthetic training loop on CPU.

    Returns the per-step loss trace. Two calls with the same seed, data, and
    hyperparameters return identical traces.
    """
    torch.manual_seed(seed)
    generator = seeded_generator(seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    model.train()
    losses: list[float] = []
    for _ in range(steps):
        batch = sample_episode_batch(
            pool_x=pool_x,
            pool_y=pool_y,
            batch_size=batch_size,
            context_size=context_size,
            generator=generator,
        )
        prediction = model(batch.context_x, batch.context_y, batch.target_x)
        loss = gaussian_nll(batch.target_y, prediction.mean, prediction.scale)

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))

    return SmokeResult(
        losses=losses,
        initial_loss=losses[0],
        final_loss=losses[-1],
    )


def overfit_single_episode(
    model: nn.Module,
    pool_x: torch.Tensor,
    pool_y: torch.Tensor,
    seed: int,
    steps: int,
    context_size: int,
    learning_rate: float,
) -> SmokeResult:
    """Drive one fixed synthetic episode to a low loss.

    Freeze section 9 item 8 requires each arm to be able to overfit a tiny
    synthetic fixture. The same episode is reused every step.
    """
    torch.manual_seed(seed)
    generator = seeded_generator(seed)
    batch = sample_episode_batch(
        pool_x=pool_x,
        pool_y=pool_y,
        batch_size=1,
        context_size=context_size,
        generator=generator,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    model.train()
    losses: list[float] = []
    for _ in range(steps):
        prediction = model(batch.context_x, batch.context_y, batch.target_x)
        loss = gaussian_nll(batch.target_y, prediction.mean, prediction.scale)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))

    return SmokeResult(
        losses=losses,
        initial_loss=losses[0],
        final_loss=losses[-1],
    )


def build_synthetic_pool(
    config: dict[str, Any], seed: int
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Generate the synthetic pool described by the configuration."""
    pool_config = SyntheticPoolConfig(
        pool_days=config["synthetic"]["pool_days"],
        feature_dim=config["synthetic"]["feature_dim"],
        horizon=config["horizon"],
    )
    return make_synthetic_pool(pool_config, seeded_generator(seed))
