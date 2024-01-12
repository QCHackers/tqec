import cirq

from tqec.noise_models import BaseNoiseModel


class AfterResetFlipNoise(BaseNoiseModel):
    def __init__(self, p: float):
        super().__init__(p)

    def noisy_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        """Applies a X flip noise after each reset operation.

        This noise model only works on cirq.ResetChannel instances! If your quantum
        circuit contains operations like the stim "MR" (Measurement and Reset)
        instruction, this noise channel will **not** add any noise.

        :param p: strength (probability of error) of the applied noise.
        """
        if isinstance(operation.gate, cirq.ResetChannel):
            return [
                operation,
                [
                    cirq.bit_flip(self.prob).on(qubit).with_tags(cirq.VirtualTag())
                    for qubit in operation.qubits
                ],
            ]
        else:
            return self.recurse_in_operation_if_CircuitOperation(operation)
