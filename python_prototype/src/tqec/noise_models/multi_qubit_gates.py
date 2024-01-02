import cirq

from tqec.noise_models import BaseNoiseModel


class MultiQubitDepolarizingNoiseAfterMultiQubitGate(BaseNoiseModel):
    def __init__(self, p: float):
        super().__init__(p)

    def noisy_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        qubit_number = len(operation.qubits)
        if qubit_number > 1:
            if isinstance(operation, cirq.CircuitOperation):
                return self.recurse_in_operation_if_CircuitOperation(operation)
            else:
                return [
                    operation,
                    cirq.depolarize(self.prob, qubit_number)
                    .on(*operation.qubits)
                    .with_tags(cirq.VirtualTag()),
                ]

        return operation
