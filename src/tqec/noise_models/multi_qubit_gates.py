import cirq

from tqec.noise_models.base import BaseNoiseModel


class MultiQubitDepolarizingNoiseAfterMultiQubitGate(BaseNoiseModel):
    def __init__(self, p: float):
        """Applies a depolarizing noise after each multi-qubit operation.

        The depolarising noise applied is a cirq.DepolarizingChannel with the
        same number of qubits as the multi-qubit operation. For a number of
        qubits `n > 1`, this is different from applying `n` times a 1-qubit
        depolarizing noise to each of the involved qubits.

        :param p: strength (probability of error) of the applied noise.
        """
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
