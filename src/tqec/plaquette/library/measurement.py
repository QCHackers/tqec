import cirq

from tqec.circuit.operations.operation import make_detector
from tqec.circuit.schedule import ScheduledCircuit
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    PlaquetteQubits,
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)


def measurement_plaquette(
    qubits: PlaquetteQubits, include_detector: bool = True
) -> Plaquette:
    (syndrome_qubit,) = qubits.get_syndrome_qubits_cirq()
    data_qubits = qubits.get_data_qubits_cirq()
    measurement_qubits = [syndrome_qubit, *data_qubits]
    detector = make_detector(
        syndrome_qubit,
        [(meas_qubit - syndrome_qubit, -1) for meas_qubit in measurement_qubits],
    )
    return Plaquette(
        qubits,
        circuit=ScheduledCircuit(
            cirq.Circuit(
                [
                    cirq.Moment(
                        cirq.M(q).with_tags(Plaquette._MERGEABLE_TAG)
                        for q in data_qubits
                    ),
                    cirq.Moment(detector) if include_detector else [],
                ]
            ),
        ),
    )


def measurement_square_plaquette(include_detector: bool = True) -> Plaquette:
    return measurement_plaquette(SquarePlaquetteQubits(), include_detector)


def measurement_rounded_plaquette(
    orientation: PlaquetteOrientation, include_detector: bool = True
) -> Plaquette:
    return measurement_plaquette(RoundedPlaquetteQubits(orientation), include_detector)
