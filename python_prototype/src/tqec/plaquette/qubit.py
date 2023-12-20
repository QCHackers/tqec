from dataclasses import dataclass

from cirq import GridQubit

from tqec.enums import PlaquetteQubitType
from tqec.position import Position


@dataclass
class PlaquetteQubit:
    type_: PlaquetteQubitType
    position: Position

    def to_grid_qubit(self) -> GridQubit:
        return GridQubit(self.position.y, self.position.x)
