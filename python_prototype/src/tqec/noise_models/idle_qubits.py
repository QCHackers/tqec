from typing import Sequence
import cirq


class DepolarizingNoiseOnIdlingQubit(cirq.NoiseModel):
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
        assert moment.qubits.issubset(
            system_qubits
        ), f"Found a moment containing illegal qubits: {moment.qubits.difference(system_qubits)}"
        if any(len(op.qubits) > 1 for op in moment):
            idle_qubits = system_qubits.difference(moment.qubits)
            return moment.with_operations(
                cirq.depolarize(self._p).on(qubit) for qubit in idle_qubits
            )
        else:
            return moment
