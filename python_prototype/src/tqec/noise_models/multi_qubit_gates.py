import cirq

from tqec.noise_models import BaseNoiseModel


class MultiQubitDepolarizingNoiseAfterMultiQubitGate(BaseNoiseModel):
    def __init__(self, p: float):
        cirq.value.validate_probability(
            p, "multi-qubit depolarizing noise after multi-qubit operation probability"
        )
        self._p = p
        super().__init__()

    def noisy_operation(self, op: cirq.Operation) -> cirq.OP_TREE:
        qubit_number = len(op.qubits)
        if qubit_number > 1:
            if isinstance(op, cirq.CircuitOperation):
                return self.recurse_in_operation_if_CircuitOperation(op)
            else:
                return [
                    op,
                    cirq.depolarize(self._p, qubit_number).on(*op.qubits),
                ]

        return op
