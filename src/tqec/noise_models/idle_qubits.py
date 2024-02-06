from typing import Sequence

import cirq
from tqec.noise_models.base import BaseNoiseModel


class DepolarizingNoiseOnIdlingQubit(BaseNoiseModel):
    def __init__(self, p: float):
        """Applies a depolarizing noise on all idle qubits.

        Idle qubits are computed on a per-Moment basis: any qubit that has no
        operation applied on in a Moment that contains a multi-qubit gate is
        considered idle during this Moment and a depolarizing noise is added
        to account for this idle time.

        :param p: strength (probability of error) of the applied noise.
        """
        super().__init__(p)

    def noisy_moment(
        self, moment: cirq.Moment, system_qubits: Sequence[cirq.Qid]
    ) -> cirq.OP_TREE:
        # Noise should not be appended to previously-added noise.
        if self.is_virtual_moment(moment):
            return moment

        system_qubits_set = set(system_qubits)

        # Apply recursively the noise model to CircuitOperation instances
        moment = cirq.Moment(
            self.recurse_in_operation_if_circuit_operation(op) for op in moment
        )
        # Apply the noise model to the moment at hand, not recursing into
        # any CircuitOperation instances
        if any(len(op.qubits) > 1 for op in moment):
            idle_qubits = system_qubits_set.difference(moment.qubits)
            moment = moment.with_operations(
                cirq.depolarize(self.prob).on(qubit).with_tags(cirq.VirtualTag())
                for qubit in idle_qubits
            )
        # Return the modified moment
        return moment
