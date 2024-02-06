import cirq
import stim

from tqec.noise_models.base import BaseNoiseModel


def is_clifford(operation: cirq.Operation) -> bool:
    """Inefficiently checks if a given operation implements a Clifford operation

    The check is implemented by recovering the unitary matrix of the operation and
    trying to initialise a stim.Tableau from it. Both steps are costly for large
    operations, which is the reason why this function will print a warning if the
    provided operation is considered "large" (3 qubits or more at the moment).

    :param operation: the operation that will be checked.
    :returns: True if the provided cirq.Operation instance is a Clifford operation,
        else False.
    """
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
        """Applies a depolarising noise after each Clifford operation.

        The depolarising noise applied is a cirq.DepolarizingChannel with the same
        number of qubits as the Clifford operation. For a number of qubits `n > 1`,
        this is different from applying `n` times a 1-qubit depolarizing noise to each
        of the involved qubits.

        :param p: strength (probability of error) of the applied noise.
        """
        super().__init__(p)

    def noisy_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        if isinstance(operation, cirq.CircuitOperation):
            return self.recurse_in_operation_if_circuit_operation(operation)
        elif is_clifford(operation):
            return [
                operation,
                cirq.depolarize(self.prob, n_qubits=len(operation.qubits))
                .on(*operation.qubits)
                .with_tags(cirq.VirtualTag()),
            ]
        else:
            return operation
