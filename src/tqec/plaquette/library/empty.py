import cirq

from tqec.circuit.schedule import ScheduledCircuit
from tqec.enums import PlaquetteOrientation
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


class EmptyPlaquette(Plaquette):
    def __init__(self, qubits: PlaquetteQubits) -> None:
        super().__init__(qubits, ScheduledCircuit(cirq.Circuit()))


class EmptySquarePlaquette(EmptyPlaquette):
    def __init__(self) -> None:
        super().__init__(SquarePlaquetteQubits())


class EmptyRoundedPlaquette(EmptyPlaquette):
    def __init__(self, orientation: PlaquetteOrientation) -> None:
        super().__init__(RoundedPlaquetteQubits(orientation))
