"""Fixtures for the Track A synthetic scaffold tests.

Synthetic fixtures only. No real ERCOT, EIA, weather, event, or censoring
artifact is loaded by any fixture here.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from ercot_forecasting.track_a.train import (
    build_adacnp,
    build_cnp,
    build_synthetic_pool,
    load_scaffold_config,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "configs" / "track_a" / "scaffold_synthetic.yaml"

# A small pool keeps the tests fast; the headline context size of 64 is used
# where the freeze's value matters.
TEST_POOL_DAYS = 96
TEST_CONTEXT_SIZE = 16


@pytest.fixture(scope="session")
def scaffold_config() -> dict:
    """The frozen scaffold configuration."""
    return load_scaffold_config(CONFIG_PATH)


@pytest.fixture(scope="session")
def primary_seed(scaffold_config: dict) -> int:
    """The first frozen seed (freeze section 8)."""
    return int(scaffold_config["seeds"][0])


@pytest.fixture
def small_config(scaffold_config: dict) -> dict:
    """Configuration with a smaller synthetic pool, for fast tests."""
    config = {key: value for key, value in scaffold_config.items()}
    config["synthetic"] = dict(scaffold_config["synthetic"])
    config["synthetic"]["pool_days"] = TEST_POOL_DAYS
    return config


@pytest.fixture
def synthetic_pool(
    small_config: dict, primary_seed: int
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """A generated synthetic pool of days."""
    return build_synthetic_pool(small_config, primary_seed)


@pytest.fixture
def cnp_model(small_config: dict, primary_seed: int):
    """CNP arm at the first frozen seed."""
    return build_cnp(small_config, primary_seed)


@pytest.fixture
def adacnp_model(small_config: dict, primary_seed: int):
    """AdaCNP arm at the first frozen seed."""
    return build_adacnp(small_config, primary_seed)
