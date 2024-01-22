from dataclasses import dataclass

from cirq import GridQubit

from tqec.position import Position


@dataclass
class PlaquetteQubit:
    """Defines a qubit in the plaquette coordinate system

    This class initially had more attributes, which ended-up being flagged
    as superfluous and so have been removed.
    For now, it only stores the position of the qubit in the plaquette
    coordinate system and implements an helper method to get a cirq.GridQubit
    instance.
    """

    position: Position

    def to_grid_qubit(self) -> GridQubit:
        # GridQubit are indexed as (row, col)
        return GridQubit(self.position.y, self.position.x)
