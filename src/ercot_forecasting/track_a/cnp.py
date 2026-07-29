"""Standard Conditional Neural Process (CNP arm).

Assembles encoder, aggregator, and decoder into the architecture of CNP
Eqs. (1)-(3). The shared assembly lives here and is reused verbatim by the
AdaCNP arm, so freeze section 2's requirement that the arms share encoder and
decoder is enforced by construction rather than by matching two code paths.

Submodules are built in a fixed order -- encoder, then decoder, then aggregator
-- so that for a given seed both arms draw identical encoder and decoder
initialisations, and only the aggregator's parameters differ.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from torch import Tensor, nn

from ercot_forecasting.track_a.aggregation import UniformMeanAggregator
from ercot_forecasting.track_a.decoder import DecoderConfig, GaussianDecoder
from ercot_forecasting.track_a.encoder import ContextEncoder, EncoderConfig


@dataclass(frozen=True)
class ModelConfig:
    """Architecture shared by both arms (freeze section 2)."""

    feature_dim: int
    horizon: int
    representation_dim: int
    encoder_hidden: int
    decoder_hidden: int
    scale_floor: float


@dataclass(frozen=True)
class Prediction:
    """Model output.

    Attributes:
        mean: ``(B, n_t, horizon)``
        scale: ``(B, n_t, horizon)`` strictly positive
        weights: ``(B, n_t, n_c)`` context weights, summing to one
    """

    mean: Tensor
    scale: Tensor
    weights: Tensor


class NeuralProcessBase(nn.Module):
    """Encoder / aggregator / decoder pipeline shared by both arms."""

    def __init__(
        self,
        config: ModelConfig,
        aggregator_factory: Callable[[], nn.Module] | None = None,
    ) -> None:
        super().__init__()
        self.config = config

        self.encoder = ContextEncoder(
            EncoderConfig(
                feature_dim=config.feature_dim,
                horizon=config.horizon,
                hidden_dim=config.encoder_hidden,
                representation_dim=config.representation_dim,
            )
        )
        self.decoder = GaussianDecoder(
            DecoderConfig(
                feature_dim=config.feature_dim,
                representation_dim=config.representation_dim,
                hidden_dim=config.decoder_hidden,
                horizon=config.horizon,
                scale_floor=config.scale_floor,
            )
        )
        # The aggregator is constructed here, after the encoder and decoder, so
        # that at a common seed both arms draw identical encoder and decoder
        # initialisations and only the aggregator's parameters differ. Passing a
        # factory rather than a built module is what enforces that ordering: an
        # already-constructed aggregator would have consumed its random draws
        # first and shifted the shared parameters.
        self.aggregator = (
            aggregator_factory()
            if aggregator_factory is not None
            else UniformMeanAggregator()
        )

    def forward(
        self,
        context_x: Tensor,
        context_y: Tensor,
        target_x: Tensor,
    ) -> Prediction:
        """Run one episode batch.

        Args:
            context_x: ``(B, n_c, d_x)``
            context_y: ``(B, n_c, horizon)``
            target_x: ``(B, n_t, d_x)``

        Note that target outcomes are not a parameter. The forward pass has no
        channel through which a target ``y`` could reach aggregation.
        """
        representations = self.encoder(context_x, context_y)
        aggregated, weights = self.aggregator(representations, context_x, target_x)
        mean, scale = self.decoder(target_x, aggregated)
        return Prediction(mean=mean, scale=scale, weights=weights)


class ConditionalNeuralProcess(NeuralProcessBase):
    """CNP arm: uniform mean aggregation."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config, aggregator_factory=None)
