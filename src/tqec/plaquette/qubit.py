from __future__ import annotations

import typing as ty
from dataclasses import dataclass
from fractions import Fraction

from tqec.circuit.qubit import GridQubit
from tqec.plaquette.enums import PlaquetteOrientation, PlaquetteSide
from tqec.position import Position2D
from tqec.templates.enums import TemplateOrientation


class PlaquetteQubit(GridQubit):
    """Defines a qubit in the plaquette coordinate system.

    This class initially had more attributes, which ended-up being
    flagged as superfluous and so have been removed. For now, it only
    stores the position of the qubit in the plaquette coordinate system
    and implements an helper method to get a cirq.GridQubit instance.
    """

    pass


@dataclass(frozen=True)
class PlaquetteQubits:
    data_qubits: list[PlaquetteQubit]
    syndrome_qubits: list[PlaquetteQubit]

    def get_data_qubits(self) -> list[PlaquetteQubit]:
        return self.data_qubits

    def get_syndrome_qubits(self) -> list[PlaquetteQubit]:
        return self.syndrome_qubits

    def __iter__(self) -> ty.Iterator[PlaquetteQubit]:
        yield from self.data_qubits
        yield from self.syndrome_qubits

    def to_grid_qubit(self) -> list[GridQubit]:
        return list(self)

    def permute_data_qubits(self, permutation: ty.Sequence[int]) -> PlaquetteQubits:
        return PlaquetteQubits(
            [self.data_qubits[i] for i in permutation], self.syndrome_qubits
        )

    def get_edge_qubits(
        self,
        orientation: TemplateOrientation = TemplateOrientation.HORIZONTAL,
    ) -> list[PlaquetteQubit]:
        """Return the data qubits on the edge of the plaquette. By convention,
        the edge is the one with the highest index in the relevant axis.

        Args:
            orientation (TemplateOrientation, optional): Whether to use horizontal or
                vertical orientation as the axis. Defaults to horizontal.
        Returns:
            list[PlaquetteQubit]: The qubits on the edge of the plaquette.
        """

        def _get_relevant_value(qubit: PlaquetteQubit) -> Fraction:
            return qubit.y if orientation == TemplateOrientation.HORIZONTAL else qubit.x

        max_index = max(_get_relevant_value(q) for q in self.data_qubits)
        return [
            qubit
            for qubit in self.data_qubits
            if (_get_relevant_value(qubit) == max_index)
        ]

    def get_qubits_on_side(self, side: PlaquetteSide) -> list[PlaquetteQubit]:
        """Return the qubits one the provided side of the instance.

        A qubit is on the left-side if there is no other qubit in the instance
        with a strictly lower x-coordinate value. Similarly, a qubit is on the
        right-side if there is no other qubit in the instance with a strictly
        greater x-coordinate value. Up and down are about the y-coordinate.

        Args:
            side: the side to find qubits on.
        Returns:
            list[PlaquetteQubit]: The qubits on the edge of the plaquette.
        """
        if side == PlaquetteSide.LEFT:
            min_x = min(q.x for q in self)
            return [q for q in self if q.x == min_x]
        elif side == PlaquetteSide.RIGHT:
            max_x = max(q.x for q in self)
            return [q for q in self if q.x == max_x]
        elif side == PlaquetteSide.UP:
            min_y = min(q.y for q in self)
            return [q for q in self if q.y == min_y]
        else:  # if orientation == PlaquetteSide.DOWN:
            max_y = max(q.y for q in self)
            return [q for q in self if q.y == max_y]


class SquarePlaquetteQubits(PlaquetteQubits):
    def __init__(self) -> None:
        super().__init__(
            [
                PlaquetteQubit(-1, -1),
                PlaquetteQubit(1, -1),
                PlaquetteQubit(-1, 1),
                PlaquetteQubit(1, 1),
            ],
            [PlaquetteQubit(0, 0)],
        )


class RoundedPlaquetteQubits(PlaquetteQubits):
    _POTENTIAL_DATA_QUBITS: ty.Final[list[PlaquetteQubit]] = [
        PlaquetteQubit(-1, -1),
        PlaquetteQubit(1, -1),
        PlaquetteQubit(-1, 1),
        PlaquetteQubit(1, 1),
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
            [PlaquetteQubit(0, 0)],
        )
