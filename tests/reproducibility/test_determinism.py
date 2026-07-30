"""Determinism is asserted, not printed.

Freeze §9 item 7 requires a fixed seed to reproduce a run. That was checked only
by a `print` in `scripts/run_stage3.py` — the boolean was computed, displayed,
and never asserted — and stage 4 had no check at all, despite being the stage
that produced the reported results.

These tests exercise the real-data stage-4 path end to end on one fold at a small
context size. They are slow by nature; the claim cannot be made on synthetic
fixtures, because what is under test is that *this* pipeline reproduces.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ercot_forecasting.track_a.censoring import load_censoring_index
from ercot_forecasting.track_a.context_conditions import ContextCondition
from ercot_forecasting.track_a.event_eligibility import derive_eligible_events
from ercot_forecasting.track_a.features import build_episode_arrays
from ercot_forecasting.track_a.load_data import load_harmonized
from ercot_forecasting.track_a.partition import build_loeo_folds, build_target_days
from ercot_forecasting.track_a.stage4 import (
    Stage4Config,
    build_fold_dataset,
    build_fold_episodes,
    partition_fold_days,
    run_fold_arm,
)
from ercot_forecasting.track_a.train import load_scaffold_config

REPO_ROOT = Path(__file__).resolve().parents[2]
LOAD = REPO_ROOT / "data" / "frozen" / "track_a" / "ercot_hourly_load_harmonized.csv"
INVENTORY = REPO_ROOT / "data" / "shared" / "event_inventory_headline.csv"
CENSORING = REPO_ROOT / "data" / "frozen" / "track_a" / "v7_demand_censored_v3.csv"
SCAFFOLD = REPO_ROOT / "configs" / "track_a" / "scaffold_synthetic.yaml"

pytestmark = pytest.mark.skipif(
    not (LOAD.is_file() and INVENTORY.is_file() and CENSORING.is_file()),
    reason="Track A artifacts not imported",
)

SEED = 20260729
TEST_CONTEXT_SIZE = 8
TEST_STEPS = 60


@pytest.fixture(scope="module")
def fold_setup():
    load = load_harmonized(LOAD, usable_only=True)
    eligible = derive_eligible_events(INVENTORY, LOAD)
    index = build_target_days(load)
    episodes = build_episode_arrays(load, index)
    fold = build_loeo_folds(eligible)[0]
    partition = partition_fold_days(load, fold, index)
    dataset = build_fold_dataset(load, partition, index, episodes)
    return dataset, load_censoring_index(CENSORING), load_scaffold_config(SCAFFOLD)


def _config(condition: ContextCondition = ContextCondition.NEAREST) -> Stage4Config:
    return Stage4Config(
        seed=SEED,
        context_size=TEST_CONTEXT_SIZE,
        steps=TEST_STEPS,
        eval_every=TEST_STEPS,
        context_condition=condition,
    )


def test_repeated_run_reproduces_the_metric(fold_setup, tmp_path) -> None:
    """Two runs at one seed give bitwise-equal primary NLL and loss trace."""
    dataset, censoring, scaffold = fold_setup
    config = _config()
    train_episodes, event_episodes = build_fold_episodes(dataset, config, tmp_path)

    first = run_fold_arm(
        "CNP", scaffold, dataset, train_episodes, event_episodes, censoring, config
    )
    second = run_fold_arm(
        "CNP", scaffold, dataset, train_episodes, event_episodes, censoring, config
    )

    assert first.score.primary_nll == second.score.primary_nll
    assert first.score.served_load_nll == second.score.served_load_nll
    assert first.initial_loss == second.initial_loss
    assert first.final_loss == second.final_loss
    assert first.selected_step == second.selected_step


def test_both_arms_consume_one_context_file(fold_setup, tmp_path) -> None:
    """The arms differ in architecture, never in the context they were given."""
    dataset, censoring, scaffold = fold_setup
    config = _config()
    train_episodes, event_episodes = build_fold_episodes(dataset, config, tmp_path)

    hashes = {
        run_fold_arm(
            arm, scaffold, dataset, train_episodes, event_episodes, censoring, config
        ).context_file_sha256
        for arm in ("CNP", "AdaCNP")
    }
    assert len(hashes) == 1


def test_arms_produce_different_predictions(fold_setup, tmp_path) -> None:
    """The two arms are not accidentally the same model.

    The suite proves at length that AdaCNP *collapses to* CNP when its weights
    are forced uniform. Nothing proved the converse — that with learned weights
    they actually differ — so a wiring bug that silently ran CNP twice would
    have gone unnoticed.
    """
    dataset, censoring, scaffold = fold_setup
    config = _config()
    train_episodes, event_episodes = build_fold_episodes(dataset, config, tmp_path)

    cnp = run_fold_arm(
        "CNP", scaffold, dataset, train_episodes, event_episodes, censoring, config
    )
    ada = run_fold_arm(
        "AdaCNP", scaffold, dataset, train_episodes, event_episodes, censoring, config
    )

    assert ada.trainable_parameters > cnp.trainable_parameters
    assert cnp.score.primary_nll != ada.score.primary_nll


def test_sampled_condition_is_seed_reproducible(fold_setup, tmp_path) -> None:
    """The paper-faithful sampled context is deterministic under the frozen seed."""
    dataset, _censoring, _scaffold = fold_setup
    config = _config(ContextCondition.SAMPLED)

    first, _ = build_fold_episodes(dataset, config, tmp_path / "a")
    second, _ = build_fold_episodes(dataset, config, tmp_path / "b")

    assert first.context_file.sha256 == second.context_file.sha256
    assert (first.context_indices == second.context_indices).all()


def test_sampled_and_nearest_differ(fold_setup, tmp_path) -> None:
    """The two conditions really do select different context sets (D-013)."""
    dataset, _censoring, _scaffold = fold_setup

    nearest, _ = build_fold_episodes(
        dataset, _config(ContextCondition.NEAREST), tmp_path / "n"
    )
    sampled, _ = build_fold_episodes(
        dataset, _config(ContextCondition.SAMPLED), tmp_path / "s"
    )

    assert nearest.context_file.sha256 != sampled.context_file.sha256
