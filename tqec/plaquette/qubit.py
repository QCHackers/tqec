from dataclasses import dataclass

from cirq import GridQubit

from tqec.position import Position


@dataclass
class PlaquetteQubit:
    position: Position

    def to_grid_qubit(self) -> GridQubit:
        # GridQubit are indexed as (row, col)
        return GridQubit(self.position.y, self.position.x)
