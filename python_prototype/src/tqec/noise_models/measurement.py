import cirq


class XNoiseBeforeMeasurement(cirq.NoiseModel):
    def __init__(self, p: float):
        self._p = p
        super().__init__()

    def noisy_operation(self, op: cirq.Operation) -> cirq.OP_TREE:
        if isinstance(op.gate, cirq.MeasurementGate):
            return [cirq.bit_flip(self._p).on_each(*op.qubits), op]
        return op
