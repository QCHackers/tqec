from __future__ import annotations

import cirq

from tqec.plaquette.library.utils.detectors import make_memory_experiment_detector
from tqec.plaquette.library.utils.pauli import make_pauli_syndrome_measurement_circuit
from tqec.plaquette.plaquette import SquarePlaquette
from tqec.plaquette.schedule import ScheduledCircuit


class XXXXMemoryPlaquette(SquarePlaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
        is_first_round: bool = False,
    ):
        (syndrome_qubit,) = SquarePlaquette.get_syndrome_qubits()
        data_qubits = SquarePlaquette.get_data_qubits()

        circuit = make_pauli_syndrome_measurement_circuit(
            syndrome_qubit, data_qubits, "XXXX"
        )
        if include_detector:
            circuit.append(
                cirq.Moment(
                    make_memory_experiment_detector(syndrome_qubit, is_first_round)
                )
            )

        super().__init__(ScheduledCircuit(circuit, schedule))
