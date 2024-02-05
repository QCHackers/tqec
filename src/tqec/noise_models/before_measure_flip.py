import cirq

from tqec.noise_models.base import BaseNoiseModel


class BeforeMeasurementFlipNoise(BaseNoiseModel):
    def __init__(self, p: float):
        """Applies a X flip noise before each measurement operation.

        This noise model only works on cirq.MeasurementGate instances! If your quantum
        circuit contains operations like the stim "MR" (Measurement and Reset)
        instruction, this noise channel will **not** add any noise.

        :param p: strength (probability of error) of the applied noise.
        """
        super().__init__(p)

    def noisy_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        if isinstance(operation.gate, cirq.MeasurementGate):
            return [
                [
                    cirq.bit_flip(self.prob).on(qubit).with_tags(cirq.VirtualTag())
                    for qubit in operation.qubits
                ],
                operation,
            ]
        else:
            return self.recurse_in_operation_if_circuit_operation(operation)
