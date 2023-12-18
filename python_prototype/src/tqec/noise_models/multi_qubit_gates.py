import cirq


class MultiQubitDepolarizingNoiseAfterMultiQubitGate(cirq.NoiseModel):
    def __init__(self, p: float):
        self._p = p
        super().__init__()

    def noisy_operation(self, op: cirq.Operation) -> cirq.OP_TREE:
        qubit_number = len(op.qubits)
        if qubit_number > 1:
            return [op, cirq.depolarize(self._p, qubit_number).on(*op.qubits)]
        return op
