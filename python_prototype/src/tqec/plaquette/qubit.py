from dataclasses import dataclass

from cirq import GridQubit

from tqec.enums import PlaquetteQubitType
from tqec.position import Position


@dataclass
class PlaquetteQubit:
    type_: PlaquetteQubitType
    position: Position

    def to_grid_qubit(self) -> GridQubit:
        # GridQubit are indexed as (x, y)
        return GridQubit(self.position.x, self.position.y)
