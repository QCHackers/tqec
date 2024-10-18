"""Defines empty plaquettes with an empty circuit."""

from tqec.circuit.schedule import ScheduledCircuit
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    PlaquetteQubits,
    SquarePlaquetteQubits,
)


def empty_plaquette(qubits: PlaquetteQubits) -> Plaquette:
    return Plaquette("empty", qubits, ScheduledCircuit.empty())


def empty_square_plaquette() -> Plaquette:
    return empty_plaquette(SquarePlaquetteQubits())
