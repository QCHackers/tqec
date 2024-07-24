from __future__ import annotations

from tqec.exceptions import TQECException
from tqec.templates.atomic.rectangle import (
    AlternatingRectangleTemplate,
    RawRectangleTemplate,
)
from tqec.templates.atomic.square import AlternatingSquareTemplate
from tqec.templates.base import TemplateWithIndices
from tqec.templates.composed import ComposedTemplate
from tqec.templates.enums import (
    BELOW_OF,
    RIGHT_OF,
    TemplateOrientation,
    TemplateSide,
)
from tqec.templates.scale import LinearFunction


class DenseQubitSquareTemplate(ComposedTemplate):
    def __init__(
        self,
        dim: LinearFunction,
        k: int = 2,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        """An error-corrected qubit.

        The below text represents this template for an input ``dimension = FixedDimension(4)`` ::

            1  5  6  5  6  2
            7  9 10  9 10 11
            8 10  9 10  9 12
            7  9 10  9 10 11
            8 10  9 10  9 12
            3 13 14 13 14  4

        Args:
            dim: dimension of the error-corrected qubit.
            k: initial value for the scaling parameter.
        """
        # nsone: non-scalable one
        nsone = LinearFunction(0, 1)

        # 0  4  4  4  4  1
        # 5  6  6  6  6  7
        # 5  6  6  6  6  7
        # 5  6  6  6  6  7
        # 5  6  6  6  6  7
        # 2  8  8  8  8  3
        _templates = [
            TemplateWithIndices(RawRectangleTemplate([[0]]), [1]),
            TemplateWithIndices(RawRectangleTemplate([[0]]), [2]),
            TemplateWithIndices(RawRectangleTemplate([[0]]), [3]),
            TemplateWithIndices(RawRectangleTemplate([[0]]), [4]),
            # Top rectangle, containing plaquettes of type 5 and 6
            TemplateWithIndices(AlternatingRectangleTemplate(dim, nsone), [5, 6]),
            # Left rectangle, containing plaquettes of type 7 and 8
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, dim), [7, 8]),
            # Central square, containing plaquettes of types 9 and 10
            TemplateWithIndices(AlternatingSquareTemplate(dim), [9, 10]),
            # Right rectangle, containing plaquettes of type 11 and 12
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, dim), [11, 12]),
            # Bottom rectangle, containing plaquettes of type 13 and 14
            TemplateWithIndices(AlternatingRectangleTemplate(dim, nsone), [13, 14]),
        ]
        self._side_indices: dict[TemplateSide, list[int]] = {
            TemplateSide.BOTTOM: _templates[8].indices,
            TemplateSide.BOTTOM_LEFT: _templates[2].indices,
            TemplateSide.BOTTOM_RIGHT: _templates[3].indices,
            TemplateSide.LEFT: _templates[5].indices,
            TemplateSide.RIGHT: _templates[7].indices,
            TemplateSide.TOP: _templates[4].indices,
            TemplateSide.TOP_LEFT: _templates[0].indices,
            TemplateSide.TOP_RIGHT: _templates[1].indices,
        }
        _relations = [
            (5, BELOW_OF, 0),
            (2, BELOW_OF, 5),
            (4, RIGHT_OF, 0),
            (1, RIGHT_OF, 4),
            (6, RIGHT_OF, 5),
            (7, RIGHT_OF, 6),
            (8, BELOW_OF, 6),
            (3, RIGHT_OF, 8),
        ]
        super().__init__(
            _templates,
            k=k,
            default_x_increment=default_x_increment,
            default_y_increment=default_y_increment,
        )
        for source, relpos, target in _relations:
            self.add_relation(source, relpos, target)

    def get_midline_plaquettes(
        self, orientation: TemplateOrientation = TemplateOrientation.HORIZONTAL
    ) -> list[tuple[int, int]]:
        midline_shape, iteration_shape = self.shape.x, self.shape.y
        if midline_shape % 2 == 1:
            raise TQECException(
                "Midline is not defined for odd "
                + f"{'height' if orientation == TemplateOrientation.HORIZONTAL else 'width'}."
            )
        midline = midline_shape // 2 - 1
        if orientation == TemplateOrientation.VERTICAL:
            return [(row, midline) for row in range(iteration_shape)]
        return [(midline, column) for column in range(iteration_shape)]

    def get_plaquette_indices_on_sides(self, sides: list[TemplateSide]) -> list[int]:
        return sorted(sum((self._side_indices[side] for side in sides), start=[]))
