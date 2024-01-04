from dataclasses import dataclass

from cirq import GridQubit

from tqec.position import Position


@dataclass
class PlaquetteQubit:
    position: Position

    def to_grid_qubit(self) -> GridQubit:
        # GridQubit are indexed as (x, y)
        return GridQubit(self.position.x, self.position.y)
