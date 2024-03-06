from __future__ import annotations

import typing as ty
from dataclasses import dataclass

import cirq

from tqec.enums import PlaquetteOrientation, PlaquetteSide
from tqec.position import Position


@dataclass(frozen=True)
class PlaquetteQubit:
    """Defines a qubit in the plaquette coordinate system

    This class initially had more attributes, which ended-up being flagged
    as superfluous and so have been removed.
    For now, it only stores the position of the qubit in the plaquette
    coordinate system and implements an helper method to get a cirq.GridQubit
    instance.
    """

    position: Position

    def to_grid_qubit(self) -> cirq.GridQubit:
        # GridQubit are indexed as (row, col)
        return cirq.GridQubit(self.position.y, self.position.x)


@dataclass(frozen=True)
class PlaquetteQubits:
    data_qubits: list[PlaquetteQubit]
    syndrome_qubits: list[PlaquetteQubit]

    def get_data_qubits(self) -> list[PlaquetteQubit]:
        return self.data_qubits

    def get_syndrome_qubits(self) -> list[PlaquetteQubit]:
        return self.syndrome_qubits

    def get_data_qubits_cirq(self) -> list[cirq.GridQubit]:
        return [q.to_grid_qubit() for q in self.get_data_qubits()]

    def get_syndrome_qubits_cirq(self) -> list[cirq.GridQubit]:
        return [q.to_grid_qubit() for q in self.get_syndrome_qubits()]

    def __iter__(self):
        yield from self.data_qubits
        yield from self.syndrome_qubits

    def to_grid_qubit(self) -> list[cirq.GridQubit]:
        # GridQubit are indexed as (row, col)
        return [q.to_grid_qubit() for q in self]

    def permute_data_qubits(self, permutation: ty.Sequence[int]) -> PlaquetteQubits:
        return PlaquetteQubits(
            [self.data_qubits[i] for i in permutation], self.syndrome_qubits
        )


class SquarePlaquetteQubits(PlaquetteQubits):
    def __init__(self):
        super().__init__(
            [
                PlaquetteQubit(Position(-1, -1)),
                PlaquetteQubit(Position(1, -1)),
                PlaquetteQubit(Position(-1, 1)),
                PlaquetteQubit(Position(1, 1)),
            ],
            [PlaquetteQubit(Position(0, 0))],
        )


class RoundedPlaquetteQubits(PlaquetteQubits):
    _POTENTIAL_DATA_QUBITS: ty.Final[list[PlaquetteQubit]] = [
        PlaquetteQubit(Position(-1, -1)),
        PlaquetteQubit(Position(1, -1)),
        PlaquetteQubit(Position(-1, 1)),
        PlaquetteQubit(Position(1, 1)),
    ]

    @staticmethod
    def _get_qubits_on_side(side: PlaquetteSide) -> list[PlaquetteQubit]:
        data_indices: tuple[int, int]
        if side == PlaquetteSide.LEFT:
            data_indices = (0, 2)
        elif side == PlaquetteSide.RIGHT:
            data_indices = (1, 3)
        elif side == PlaquetteSide.UP:
            data_indices = (0, 1)
        else:  # if orientation == PlaquetteSide.DOWN:
            data_indices = (2, 3)
        return [RoundedPlaquetteQubits._POTENTIAL_DATA_QUBITS[i] for i in data_indices]

    def __init__(self, orientation: PlaquetteOrientation):
        super().__init__(
            RoundedPlaquetteQubits._get_qubits_on_side(orientation.to_plaquette_side()),
            [PlaquetteQubit(Position(0, 0))],
        )
