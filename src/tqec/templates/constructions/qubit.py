from __future__ import annotations

from tqec.enums import ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF, TemplateOrientation
from tqec.exceptions import TQECException
from tqec.templates.atomic.rectangle import AlternatingRectangleTemplate
from tqec.templates.atomic.square import AlternatingSquareTemplate
from tqec.templates.base import TemplateWithIndices
from tqec.templates.composed import ComposedTemplate
from tqec.templates.scale import Dimension, FixedDimension


class QubitSquareTemplate(ComposedTemplate):
    def __init__(self, dim: Dimension) -> None:
        """An error-corrected qubit.

        The below text represents this template for an input ``dimension = FixedDimension(4)`` ::

            .  .  1  .  1  .
            2  3  4  3  4  .
            .  4  3  4  3  5
            2  3  4  3  4  .
            .  4  3  4  3  5
            .  6  .  6  .  .

        Args:
            dim: dimension of the error-corrected qubit.
        """
        # nsone: non-scalable one
        nsone = FixedDimension(1)

        _templates = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithIndices(AlternatingSquareTemplate(dim), [3, 4]),
            # Top rectangle, containing plaquettes of type 1 only
            TemplateWithIndices(AlternatingRectangleTemplate(dim, nsone), [0, 1]),
            # Left rectangle, containing plaquettes of type 2 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, dim), [2, 0]),
            # Right rectangle, containing plaquettes of type 5 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, dim), [0, 5]),
            # Bottom rectangle, containing plaquettes of type 6 only
            TemplateWithIndices(AlternatingRectangleTemplate(dim, nsone), [6, 0]),
        ]
        _relations = [
            (1, ABOVE_OF, 0),
            (2, LEFT_OF, 0),
            (3, RIGHT_OF, 0),
            (4, BELOW_OF, 0),
        ]
        super().__init__(_templates)
        for source, relpos, target in _relations:
            self.add_relation(source, relpos, target)

    def get_midline_plaquettes(
        self, orientation: TemplateOrientation = TemplateOrientation.HORIZONTAL
    ) -> list[tuple[int, int]]:
        midline_shape, iteration_shape = self.shape.x.value, self.shape.y.value
        if midline_shape % 2 == 1:
            raise TQECException(
                "Midline is not defined for odd "
                + f"{'height' if orientation == TemplateOrientation.HORIZONTAL else 'width'}."
            )
        midline = midline_shape // 2 - 1
        if orientation == TemplateOrientation.VERTICAL:
            return [(row, midline) for row in range(iteration_shape)]
        return [(midline, column) for column in range(iteration_shape)]


class QubitRectangleTemplate(ComposedTemplate):
    def __init__(
        self,
        width: Dimension,
        height: Dimension,
    ) -> None:
        """A scalable rectangle error-corrected qubit.

        The below text represents this template for an input ``width = FixedDimension(6)``
        and ``height = FixedDimension(4)`` ::

            .  .  1  .  1  .  1  .
            2  3  4  3  4  3  4  .
            .  4  3  4  3  4  3  5
            2  3  4  3  4  3  4  .
            .  4  3  4  3  4  3  5
            .  6  .  6  .  6  .  .

        Args:
            width: width of the rectangle logical qubit.
            height: height of the rectangle logical qubit.
        """
        # nsone: non-scalable one
        nsone = FixedDimension(1)

        _templates = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithIndices(AlternatingRectangleTemplate(width, height), [3, 4]),
            # Top rectangle, containing plaquettes of type 1 only
            TemplateWithIndices(AlternatingRectangleTemplate(width, nsone), [0, 1]),
            # Left rectangle, containing plaquettes of type 2 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, height), [2, 0]),
            # Right rectangle, containing plaquettes of type 5 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, height), [0, 5]),
            # Bottom rectangle, containing plaquettes of type 6 only
            TemplateWithIndices(AlternatingRectangleTemplate(width, nsone), [6, 0]),
        ]
        _relations = [
            (1, ABOVE_OF, 0),
            (2, LEFT_OF, 0),
            (3, RIGHT_OF, 0),
            (4, BELOW_OF, 0),
        ]
        super().__init__(_templates)
        for source, relpos, target in _relations:
            self.add_relation(source, relpos, target)

    def get_midline_plaquettes(
        self, orientation: TemplateOrientation = TemplateOrientation.HORIZONTAL
    ) -> list[tuple[int, int]]:
        midline_shape, iteration_shape = self.shape.x.value, self.shape.y.value
        if orientation == TemplateOrientation.VERTICAL:
            midline_shape, iteration_shape = iteration_shape, midline_shape

        if midline_shape % 2 == 1:
            raise TQECException(
                "Midline is not defined for odd "
                + f"{'height' if orientation == TemplateOrientation.HORIZONTAL else 'width'}."
            )
        midline = midline_shape // 2 - 1
        if orientation == TemplateOrientation.VERTICAL:
            return [(row, midline) for row in range(iteration_shape)]
        return [(midline, column) for column in range(iteration_shape)]
