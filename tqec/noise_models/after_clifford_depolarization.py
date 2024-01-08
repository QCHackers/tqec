import cirq
import stim

from tqec.noise_models import BaseNoiseModel


def is_clifford(operation: cirq.Operation) -> bool:
    try:
        num_qubits = len(operation.qubits)
        if num_qubits > 2:
            print(f"Warning: checking if an operation with {num_qubits} is Clifford.")
        matrix = cirq.protocols.unitary(operation.gate)
        stim.Tableau.from_unitary_matrix(matrix, endian="little")
    except TypeError:
        # Could not retrieve the operation unitary matrix
        return False
    except ValueError:
        # Operation is not a Clifford operation
        return False
    else:
        # No exception thrown, operation is a Clifford operation
        return True


class AfterCliffordDepolarizingNoise(BaseNoiseModel):
    def __init__(self, p: float):
        super().__init__(p)

    def noisy_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        if isinstance(operation, cirq.CircuitOperation):
            return self.recurse_in_operation_if_CircuitOperation(operation)
        elif is_clifford(operation):
            return [
                operation,
                cirq.depolarize(self.prob, n_qubits=len(operation.qubits))
                .on(*operation.qubits)
                .with_tags(cirq.VirtualTag()),
            ]
        else:
            return operation
