from tqec.templates.base import Template
from tqec.templates.scalable.rectangle import ScalableRectangle
from tqec.templates.scalable.base import ScalableTemplate
from tqec.templates.shapes.square import AlternatingCornerSquare
from tqec.enums import CornerPositionEnum


class ScalableAlternatingSquare(ScalableRectangle):
    def __init__(self, dimension: int) -> None:
        super().__init__(dimension, dimension)


class ScalableAlternatingCornerSquare(ScalableTemplate):
    def __init__(
        self,
        dimension: int,
        corner_position: CornerPositionEnum,
    ) -> None:
        super().__init__(AlternatingCornerSquare(dimension, corner_position))

    def scale_to(self, k: int) -> Template:
        # Change the underlying rectangle shape parameters
        self.shape_instance.set_parameters((k,))
        return self
