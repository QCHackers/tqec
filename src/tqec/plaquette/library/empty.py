import cirq

from tqec.circuit.schedule import ScheduledCircuit
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    PlaquetteQubits,
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)


def empty_plaquette(qubits: PlaquetteQubits, name: str = "empty") -> Plaquette:
    return Plaquette(name, qubits, ScheduledCircuit(cirq.Circuit()))


def empty_square_plaquette() -> Plaquette:
    return empty_plaquette(SquarePlaquetteQubits(), name="empty_square")


def empty_rounded_plaquette(orientation: PlaquetteOrientation) -> Plaquette:
    return empty_plaquette(
        RoundedPlaquetteQubits(orientation), name=f"empty_roudned_{orientation}"
    )
