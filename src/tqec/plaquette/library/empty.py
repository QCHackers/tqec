import cirq

from tqec.circuit.schedule import ScheduledCircuit
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    PlaquetteQubits,
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)


def empty_plaquette(qubits: PlaquetteQubits) -> Plaquette:
    return Plaquette(qubits, ScheduledCircuit(cirq.Circuit()))


def empty_square_plaquette() -> Plaquette:
    return empty_plaquette(SquarePlaquetteQubits())


def empty_rounded_plaquette(orientation: PlaquetteOrientation) -> Plaquette:
    return empty_plaquette(RoundedPlaquetteQubits(orientation))
