import cirq

from tqec.noise_models import BaseNoiseModel


class BeforeRoundDataDepolarizationNoise(BaseNoiseModel):
    def __init__(self, p: float):
        super().__init__(p)

    def noisy_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        raise NotImplementedError()
