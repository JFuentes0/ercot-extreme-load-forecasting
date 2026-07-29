"""Adaptive Conditional Neural Process (AdaCNP arm).

Reuses the shared encoder/decoder assembly from :mod:`cnp` and swaps in the
adaptive aggregator, so the aggregation mechanism is the only difference between
the arms (freeze section 1).

The embedding network ``phi_omega`` and scoring layer ``f_psi`` live inside the
aggregator. They are treated as internal components of the aggregation
mechanism, not as a second point of difference; that reading is recorded for
review in MODEL_MECHANICS_NOTE_v1.md section 7.3.
"""

from __future__ import annotations

from dataclasses import dataclass

from ercot_forecasting.track_a.aggregation import AdaptiveAggregator, AdaptiveConfig
from ercot_forecasting.track_a.cnp import ModelConfig, NeuralProcessBase


@dataclass(frozen=True)
class AdaptiveModelConfig:
    """AdaCNP architecture: the shared architecture plus the adaptive layer."""

    shared: ModelConfig
    embedding_dim: int
    scoring_hidden: int
    temperature: float


class AdaptiveConditionalNeuralProcess(NeuralProcessBase):
    """AdaCNP arm: target-conditioned adaptive weighting."""

    def __init__(self, config: AdaptiveModelConfig) -> None:
        # A factory, not a built module: the aggregator must be constructed
        # after the shared encoder and decoder so it does not shift their
        # random draws. See NeuralProcessBase.__init__.
        def make_aggregator() -> AdaptiveAggregator:
            return AdaptiveAggregator(
                AdaptiveConfig(
                    feature_dim=config.shared.feature_dim,
                    embedding_dim=config.embedding_dim,
                    scoring_hidden=config.scoring_hidden,
                    temperature=config.temperature,
                )
            )

        super().__init__(config.shared, aggregator_factory=make_aggregator)
        self.adaptive_config = config
