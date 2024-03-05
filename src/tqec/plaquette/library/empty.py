import cirq

from tqec.circuit.schedule import ScheduledCircuit
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    PlaquetteQubits,
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)


class EmptyPlaquette(Plaquette):
    def __init__(self, qubits: PlaquetteQubits) -> None:
        super().__init__(qubits, ScheduledCircuit(cirq.Circuit()))


class EmptySquarePlaquette(EmptyPlaquette):
    def __init__(self) -> None:
        super().__init__(SquarePlaquetteQubits())


class EmptyRoundedPlaquette(EmptyPlaquette):
    def __init__(self, orientation: PlaquetteOrientation) -> None:
        super().__init__(RoundedPlaquetteQubits(orientation))
