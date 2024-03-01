from __future__ import annotations

import cirq

from tqec.enums import PlaquetteOrientation
from tqec.plaquette.library.utils.detectors import make_memory_experiment_detector
from tqec.plaquette.library.utils.pauli import make_pauli_syndrome_measurement_circuit
from tqec.plaquette.plaquette import RoundedPlaquette
from tqec.circuit.schedule import ScheduledCircuit


class XXMemoryPlaquette(RoundedPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector: bool = True,
        is_first_round: bool = False,
    ):
        (syndrome_qubit,) = RoundedPlaquette.get_syndrome_qubits()
        data_qubits = RoundedPlaquette.get_data_qubits(orientation)

        circuit = make_pauli_syndrome_measurement_circuit(
            syndrome_qubit, data_qubits, "XX"
        )
        if include_detector:
            circuit.append(
                cirq.Moment(
                    make_memory_experiment_detector(syndrome_qubit, is_first_round)
                )
            )

        super().__init__(
            ScheduledCircuit(circuit, schedule),
            orientation,
        )
