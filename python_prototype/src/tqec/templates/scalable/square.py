from tqec.templates.base import Template
from tqec.templates.scalable.rectangle import ScalableRectangle
from tqec.templates.scalable.base import ScalableTemplate
from tqec.templates.shapes.square import AlternatingCornerSquare
from tqec.enums import CornerPositionEnum
import typing as ty


class ScalableAlternatingSquare(ScalableRectangle):
    def __init__(
        self, dimension: int, scale_func: ty.Callable[[int], int] = lambda x: x
    ) -> None:
        super().__init__(dimension, dimension, scale_func)


class ScalableAlternatingCornerSquare(ScalableTemplate):
    def __init__(
        self,
        dimension: int,
        corner_position: CornerPositionEnum,
        scale_func: ty.Callable[[int], int] = lambda x: x,
    ) -> None:
        super().__init__(
            AlternatingCornerSquare(dimension, corner_position), scale_func
        )

    def scale_to(self, k: int) -> Template:
        # Get the actual scale
        new_dimension: int = self.get_scaled_scale(k)
        # Change the underlying rectangle shape parameters
        self.shape_instance.set_parameters((new_dimension,))
        return self
