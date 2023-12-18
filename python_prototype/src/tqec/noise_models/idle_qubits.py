from typing import Sequence

import cirq

from tqec.noise_models import BaseNoiseModel


class DepolarizingNoiseOnIdlingQubit(BaseNoiseModel):
    def __init__(self, p: float):
        self._p = p
        super().__init__()

    def noisy_moment(
        self, moment: cirq.Moment, system_qubits: Sequence[cirq.Qid]
    ) -> cirq.OP_TREE:
        # Noise should not be appended to previously-added noise.
        if self.is_virtual_moment(moment):
            return moment

        system_qubits = set(system_qubits)
        illegal_qubits = moment.qubits.difference(system_qubits)
        assert (
            not illegal_qubits
        ), f"Found a moment containing illegal qubits: {illegal_qubits}"

        # Apply recursively the noise model to CircuitOperation instances
        moment = cirq.Moment.from_ops(
            *[self.recurse_in_operation_if_CircuitOperation(op) for op in moment]
        )
        # Apply the noise model to the moment at hand, not recursing into any CircuitOperation instances
        if any(len(op.qubits) > 1 for op in moment):
            idle_qubits = system_qubits.difference(moment.qubits)
            moment = moment.with_operations(
                cirq.depolarize(self._p).on(qubit) for qubit in idle_qubits
            )
        # Return the modified moment
        return moment
