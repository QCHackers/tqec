from dataclasses import dataclass

from tqec.position import Position
from tqec.enums import PlaquetteQubitType

from cirq import GridQubit


@dataclass
class PlaquetteQubit:
    type_: PlaquetteQubitType
    position: Position

    def to_grid_qubit(self) -> GridQubit:
        return GridQubit(self.position.y, self.position.x)
