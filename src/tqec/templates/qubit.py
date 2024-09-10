from typing import Sequence

import numpy
import numpy.typing as npt
from typing_extensions import override

from tqec.templates.base import RectangularTemplate
from tqec.templates.enums import TemplateSide
from tqec.templates.scale import LinearFunction, Scalable2D


class QubitTemplate(RectangularTemplate):
    """An error-corrected qubit.

    The below text represents this template for an input ``k == 2`` ::

        1  5  6  5  6  2
        7  9 10  9 10 11
        8 10  9 10  9 12
        7  9 10  9 10 11
        8 10  9 10  9 12
        3 13 14 13 14  4
    """

    @override
    def instantiate(
        self, plaquette_indices: Sequence[int] | None = None
    ) -> npt.NDArray[numpy.int_]:
        if plaquette_indices is None:
            plaquette_indices = list(range(1, self.expected_plaquettes_number + 1))

        ret = numpy.zeros(self.shape.to_numpy_shape(), dtype=numpy.int_)

        # The four corners
        ret[0, 0] = plaquette_indices[0]
        ret[0, -1] = plaquette_indices[1]
        ret[-1, 0] = plaquette_indices[2]
        ret[-1, -1] = plaquette_indices[3]
        # The up side
        ret[0, 1:-1:2] = plaquette_indices[4]
        ret[0, 2:-1:2] = plaquette_indices[5]
        # The left side
        ret[1:-1:2, 0] = plaquette_indices[6]
        ret[2:-1:2, 0] = plaquette_indices[7]
        # The center
        ret[1:-1:2, 1:-1:2] = plaquette_indices[8]
        ret[2:-1:2, 2:-1:2] = plaquette_indices[8]
        ret[1:-1:2, 2:-1:2] = plaquette_indices[9]
        ret[2:-1:2, 1:-1:2] = plaquette_indices[9]
        # The right side
        ret[1:-1:2, -1] = plaquette_indices[10]
        ret[2:-1:2, -1] = plaquette_indices[11]
        # The bottom side
        ret[-1, 1:-1:2] = plaquette_indices[12]
        ret[-1, 2:-1:2] = plaquette_indices[13]

        return ret

    @property
    @override
    def scalable_shape(self) -> Scalable2D:
        return Scalable2D(LinearFunction(2, 2), LinearFunction(2, 2))

    @property
    @override
    def expected_plaquettes_number(self) -> int:
        return 14

    @override
    def get_plaquette_indices_on_sides(self, sides: list[TemplateSide]) -> list[int]:
        indices: list[int] = []
        for side in sides:
            match side:
                case TemplateSide.TOP_LEFT:
                    indices.append(1)
                case TemplateSide.TOP_RIGHT:
                    indices.append(2)
                case TemplateSide.BOTTOM_LEFT:
                    indices.append(3)
                case TemplateSide.BOTTOM_RIGHT:
                    indices.append(4)
                case TemplateSide.TOP:
                    indices.extend((5, 6))
                case TemplateSide.LEFT:
                    indices.extend((7, 8))
                case TemplateSide.RIGHT:
                    indices.extend((11, 12))
                case TemplateSide.BOTTOM:
                    indices.extend((13, 14))
        return indices


class QubitVerticalBorders(RectangularTemplate):
    """Two vertical sides of neighbouring error-corrected qubits glued
    together.

    The below text represents this template for an input ``k == 2`` ::

        1 3
        5 7
        6 8
        5 7
        6 8
        2 4
    """

    @override
    def instantiate(
        self, plaquette_indices: Sequence[int] | None = None
    ) -> npt.NDArray[numpy.int_]:
        if plaquette_indices is None:
            plaquette_indices = list(range(1, self.expected_plaquettes_number + 1))

        ret = numpy.zeros(self.shape.to_numpy_shape(), dtype=numpy.int_)

        # The four corners
        ret[0, 0] = plaquette_indices[0]
        ret[0, -1] = plaquette_indices[1]
        ret[-1, 0] = plaquette_indices[2]
        ret[-1, -1] = plaquette_indices[3]
        # The left side
        ret[1:-1:2, 0] = plaquette_indices[4]
        ret[2:-1:2, 0] = plaquette_indices[5]
        # The right side
        ret[1:-1:2, -1] = plaquette_indices[6]
        ret[2:-1:2, -1] = plaquette_indices[7]

        return ret

    @property
    @override
    def scalable_shape(self) -> Scalable2D:
        """Returns a scalable version of the template shape."""
        return Scalable2D(LinearFunction(0, 2), LinearFunction(2, 2))

    @property
    @override
    def expected_plaquettes_number(self) -> int:
        return 8

    @override
    def get_plaquette_indices_on_sides(self, sides: list[TemplateSide]) -> list[int]:
        indices: list[int] = []
        for side in sides:
            match side:
                case TemplateSide.TOP_LEFT:
                    indices.append(1)
                case TemplateSide.TOP_RIGHT:
                    indices.append(5)
                case TemplateSide.BOTTOM_LEFT:
                    indices.append(4)
                case TemplateSide.BOTTOM_RIGHT:
                    indices.append(8)
                case TemplateSide.TOP:
                    pass
                case TemplateSide.LEFT:
                    indices.extend((2, 3))
                case TemplateSide.RIGHT:
                    indices.extend((6, 7))
                case TemplateSide.BOTTOM:
                    pass
        return indices


class QubitHorizontalBorders(RectangularTemplate):
    """Two horizontal sides of neighbouring error-corrected qubits glued
    together.

    The below text represents this template for an input ``k == 2`` ::

        1 5 6 5 6 3
        2 7 8 7 8 4
    """

    @override
    def instantiate(
        self, plaquette_indices: Sequence[int] | None = None
    ) -> npt.NDArray[numpy.int_]:
        if plaquette_indices is None:
            plaquette_indices = list(range(1, self.expected_plaquettes_number + 1))

        ret = numpy.zeros(self.shape.to_numpy_shape(), dtype=numpy.int_)

        # The four corners
        ret[0, 0] = plaquette_indices[0]
        ret[0, -1] = plaquette_indices[1]
        ret[-1, 0] = plaquette_indices[2]
        ret[-1, -1] = plaquette_indices[3]
        # The up side
        ret[0, 1:-1:2] = plaquette_indices[4]
        ret[0, 2:-1:2] = plaquette_indices[5]
        # The bottom side
        ret[-1, 1:-1:2] = plaquette_indices[6]
        ret[-1, 2:-1:2] = plaquette_indices[7]

        return ret

    @property
    @override
    def scalable_shape(self) -> Scalable2D:
        return Scalable2D(LinearFunction(2, 2), LinearFunction(0, 2))

    @property
    @override
    def expected_plaquettes_number(self) -> int:
        return 8

    @override
    def get_plaquette_indices_on_sides(self, sides: list[TemplateSide]) -> list[int]:
        indices: list[int] = []
        for side in sides:
            match side:
                case TemplateSide.TOP_LEFT:
                    indices.append(1)
                case TemplateSide.TOP_RIGHT:
                    indices.append(2)
                case TemplateSide.BOTTOM_LEFT:
                    indices.append(3)
                case TemplateSide.BOTTOM_RIGHT:
                    indices.append(4)
                case TemplateSide.TOP:
                    indices.extend((5, 6))
                case TemplateSide.LEFT:
                    pass
                case TemplateSide.RIGHT:
                    pass
                case TemplateSide.BOTTOM:
                    indices.extend((7, 8))
        return indices


class Qubit4WayJunctionTemplate(RectangularTemplate):
    """An error-corrected qubit that is making a 4-way junction with other
    logical qubits.

    The below text represents this template for an input ``k == 4`` ::

        1  5  6  5  6  5  6  5  6  2
        7 10 11 10 11 10 11 10 11 12
        8 11 10 11 10 11 10 11  9 13
        7  9 11 10 11 10 11  9 11 12
        8 11  9 11 10 11  9 11  9 13
        7  9 11  9 11 10 11  9 11 12
        8 11  9 11 10 11 10 11  9 13
        7  9 11 10 11 10 11 10 11 12
        8 11 10 11 10 11 10 11 10 13
        3 14 15 14 15 14 15 14 15  4
    """

    @override
    def instantiate(
        self, plaquette_indices: Sequence[int] | None = None
    ) -> npt.NDArray[numpy.int_]:
        if plaquette_indices is None:
            plaquette_indices = list(range(1, self.expected_plaquettes_number + 1))

        ret = numpy.zeros(self.shape.to_numpy_shape(), dtype=numpy.int_)
        size = self.shape.x

        # The four corners
        ret[0, 0] = plaquette_indices[0]
        ret[0, -1] = plaquette_indices[1]
        ret[-1, 0] = plaquette_indices[2]
        ret[-1, -1] = plaquette_indices[3]
        # The up side
        ret[0, 1:-1:2] = plaquette_indices[4]
        ret[0, 2:-1:2] = plaquette_indices[5]
        # The left side
        ret[1:-1:2, 0] = plaquette_indices[6]
        ret[2:-1:2, 0] = plaquette_indices[7]
        # The center, which is the complex part.
        # Start by plaquette_indices[10] which is the plaquette that is
        # uniformly spread on the template
        ret[1:-1:2, 2:-1:2] = plaquette_indices[10]
        ret[2:-1:2, 1:-1:2] = plaquette_indices[10]
        # Now initialize the other plaquettes
        # Start by writing plaquette_indices[9] everywhere and
        # override with plaquette_indices[8] where needed.
        ret[1:-1:2, 1:-1:2] = plaquette_indices[9]
        ret[2:-1:2, 2:-1:2] = plaquette_indices[9]
        for i in range(1, size - 1):
            # We want (i + j) to be even, because that are the only places where
            # plaquette_indices[8] *might* be encountered. We do that directly
            # in the range expression.
            # We need to avoid 0 here because it is the border of the template.
            for j in range(1 if i % 2 == 1 else 2, size - 1, 2):
                # If the cell represented by (i, j) is:
                # - below the main diagonal and above the anti-diagonal
                if i > j and (i + j) < (size - 1):
                    ret[i, j] = plaquette_indices[8]
                elif i < j and (i + j) > (size - 1):
                    ret[i, j] = plaquette_indices[8]

        # The right side
        ret[1:-1:2, -1] = plaquette_indices[11]
        ret[2:-1:2, -1] = plaquette_indices[12]
        # The bottom side
        ret[-1, 1:-1:2] = plaquette_indices[13]
        ret[-1, 2:-1:2] = plaquette_indices[14]

        return ret

    @property
    @override
    def scalable_shape(self) -> Scalable2D:
        return Scalable2D(LinearFunction(2, 2), LinearFunction(2, 2))

    @property
    @override
    def expected_plaquettes_number(self) -> int:
        return 15

    @override
    def get_plaquette_indices_on_sides(self, sides: list[TemplateSide]) -> list[int]:
        indices: list[int] = []
        for side in sides:
            match side:
                case TemplateSide.TOP_LEFT:
                    indices.append(1)
                case TemplateSide.TOP_RIGHT:
                    indices.append(2)
                case TemplateSide.BOTTOM_LEFT:
                    indices.append(3)
                case TemplateSide.BOTTOM_RIGHT:
                    indices.append(4)
                case TemplateSide.TOP:
                    indices.extend((5, 6))
                case TemplateSide.LEFT:
                    indices.extend((7, 8))
                case TemplateSide.RIGHT:
                    indices.extend((12, 13))
                case TemplateSide.BOTTOM:
                    indices.extend((14, 15))
        return indices
