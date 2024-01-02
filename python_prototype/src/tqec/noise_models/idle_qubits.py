from typing import Sequence

import cirq

from tqec.noise_models import BaseNoiseModel


class DepolarizingNoiseOnIdlingQubit(BaseNoiseModel):
    def __init__(self, p: float):
        super().__init__(p)

    def noisy_moment(
        self, moment: cirq.Moment, system_qubits: Sequence[cirq.Qid]
    ) -> cirq.OP_TREE:
        # Noise should not be appended to previously-added noise.
        if self.is_virtual_moment(moment):
            return moment

        system_qubits_set = set(system_qubits)
        illegal_qubits = moment.qubits.difference(system_qubits_set)
        assert (
            not illegal_qubits
        ), f"Found a moment containing illegal qubits: {illegal_qubits}"

        # Apply recursively the noise model to CircuitOperation instances
        moment = cirq.Moment(
            self.recurse_in_operation_if_CircuitOperation(op) for op in moment
        )
        # Apply the noise model to the moment at hand, not recursing into any CircuitOperation instances
        if any(len(op.qubits) > 1 for op in moment):
            idle_qubits = system_qubits_set.difference(moment.qubits)
            moment = moment.with_operations(
                cirq.depolarize(self.prob).on(qubit).with_tags(cirq.VirtualTag())
                for qubit in idle_qubits
            )
        # Return the modified moment
        return moment
