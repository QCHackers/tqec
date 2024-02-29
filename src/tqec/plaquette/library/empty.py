import cirq
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import RoundedPlaquette, SquarePlaquette
from tqec.circuit.schedule import ScheduledCircuit


class EmptySquarePlaquette(SquarePlaquette):
    def __init__(self) -> None:
        super().__init__(ScheduledCircuit(cirq.Circuit()))


class EmptyRoundedPlaquette(RoundedPlaquette):
    def __init__(self, orientation: PlaquetteOrientation) -> None:
        super().__init__(ScheduledCircuit(cirq.Circuit()), orientation)
