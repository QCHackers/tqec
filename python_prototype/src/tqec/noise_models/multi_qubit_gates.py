import cirq

from tqec.noise_models import BaseNoiseModel


class MultiQubitDepolarizingNoiseAfterMultiQubitGate(BaseNoiseModel):
    def __init__(self, p: float):
        cirq.value.validate_probability(
            p, "multi-qubit depolarizing noise after multi-qubit operation probability"
        )
        self._p = p
        super().__init__()

    def noisy_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        qubit_number = len(operation.qubits)
        if qubit_number > 1:
            if isinstance(operation, cirq.CircuitOperation):
                return self.recurse_in_operation_if_CircuitOperation(operation)
            else:
                noisy_gate: cirq.DepolarizingChannel = cirq.depolarize(
                    self._p, qubit_number
                )
                return [
                    operation,
                    noisy_gate.on(*operation.qubits).with_tags(cirq.VirtualTag()),
                ]

        return operation
