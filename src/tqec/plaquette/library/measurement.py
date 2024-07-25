import cirq

from tqec.circuit.schedule import ScheduledCircuit
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    PlaquetteQubits,
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)


def measurement_plaquette(qubits: PlaquetteQubits) -> Plaquette:
    return Plaquette(
        qubits,
        circuit=ScheduledCircuit(
            cirq.Circuit(
                [
                    cirq.Moment(
                        cirq.M(q).with_tags(Plaquette._MERGEABLE_TAG)
                        for q in qubits.get_data_qubits_cirq()
                    ),
                ]
            ),
        ),
    )


def measurement_square_plaquette() -> Plaquette:
    return measurement_plaquette(SquarePlaquetteQubits())


def measurement_rounded_plaquette(orientation: PlaquetteOrientation) -> Plaquette:
    return measurement_plaquette(RoundedPlaquetteQubits(orientation))
