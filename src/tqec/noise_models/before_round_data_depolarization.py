import cirq

from tqec.noise_models.base import BaseNoiseModel


class BeforeRoundDataDepolarizationNoise(BaseNoiseModel):
    def __init__(self, p: float):
        """Applies a depolarization noise before each QEC round.

        This noise model is currently not implemented.

        :param p: strength (probability of error) of the applied noise.
        """
        super().__init__(p)

    def noisy_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        raise NotImplementedError()
