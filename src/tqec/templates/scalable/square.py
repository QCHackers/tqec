from tqec.enums import CornerPositionEnum
from tqec.exceptions import TQECException
from tqec.templates.base import Template
from tqec.templates.scalable.base import ScalableTemplate
from tqec.templates.shapes.square import AlternatingCornerSquare, AlternatingSquare


class DimensionNotEvenException(TQECException):
    def __init__(self, provided_dimension: int) -> None:
        super().__init__(
            f"The provided dimension {provided_dimension} is "
            "not even. Dimension must be even to be scalable!"
        )


class ScalableAlternatingSquare(ScalableTemplate):
    """Rectangle with scalable width or height."""

    def __init__(
        self,
        dimension: int,
    ) -> None:
        if dimension % 2 != 0:
            raise DimensionNotEvenException(dimension)
        super().__init__(AlternatingSquare(dimension))

    def scale_to(self, k: int) -> Template:
        # Change the underlying square shape parameters
        self.shape_instance.set_parameters((2 * k,))
        return self


class ScalableAlternatingCornerSquare(ScalableTemplate):
    def __init__(
        self,
        dimension: int,
        corner_position: CornerPositionEnum,
    ) -> None:
        if dimension % 2 != 0:
            raise DimensionNotEvenException(dimension)
        super().__init__(AlternatingCornerSquare(dimension, corner_position))

    def scale_to(self, k: int) -> Template:
        # Change the underlying square shape parameters
        self.shape_instance.set_parameters((2 * k,))
        return self
