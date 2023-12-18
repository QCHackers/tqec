import cirq

from tqec.noise_models import BaseNoiseModel


class XNoiseBeforeMeasurement(BaseNoiseModel):
    def __init__(self, p: float):
        self._p = p
        super().__init__()

    def noisy_operation(self, op: cirq.Operation) -> cirq.OP_TREE:
        if isinstance(op.gate, cirq.MeasurementGate):
            return [cirq.bit_flip(self._p).on_each(*op.qubits), op]
        else:
            return self.recurse_in_operation_if_CircuitOperation(op)
