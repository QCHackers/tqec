from __future__ import annotations

import cirq

from tqec.circuit.schedule import ScheduledCircuit
from tqec.plaquette.library.utils.detectors import make_memory_experiment_detector
from tqec.plaquette.library.utils.pauli import make_pauli_syndrome_measurement_circuit
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import SquarePlaquetteQubits


class XXXXMemoryPlaquette(Plaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
        is_first_round: bool = False,
    ):
        qubits = SquarePlaquetteQubits()
        (syndrome_qubit,) = qubits.get_syndrome_qubits()
        data_qubits = qubits.get_data_qubits()

        circuit = make_pauli_syndrome_measurement_circuit(
            syndrome_qubit, data_qubits, "XXXX"
        )
        if include_detector:
            circuit.append(
                cirq.Moment(
                    make_memory_experiment_detector(syndrome_qubit, is_first_round)
                )
            )

        super().__init__(qubits, ScheduledCircuit(circuit, schedule))
