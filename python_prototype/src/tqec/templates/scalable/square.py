from tqec.templates.base import Template
from tqec.templates.scalable.base import ScalableTemplate
from tqec.templates.shapes.square import AlternatingSquare, AlternatingCornerSquare
from tqec.enums import CornerPositionEnum
import typing as ty


class ScalableAlternatingSquare(ScalableTemplate, AlternatingSquare):
    def __init__(
        self, dimension: int, scale_func: ty.Callable[[int], int] = lambda x: x
    ) -> None:
        ScalableTemplate.__init__(self, scale_func)
        AlternatingSquare.__init__(self, dimension)

    def to_dict(self) -> dict[str, ty.Any]:
        ret = ScalableTemplate.to_dict(self)
        ret.update(AlternatingSquare.to_dict(self))
        return ret

    def scale_to(self, k: int) -> Template:
        return AlternatingSquare.scale_to(
            self, ScalableTemplate.get_scaled_scale(self, k)
        )


class ScalableAlternatingCornerSquare(ScalableTemplate, AlternatingCornerSquare):
    def __init__(
        self,
        dimension: int,
        corner_position: CornerPositionEnum,
        scale_func: ty.Callable[[int], int] = lambda x: x,
    ) -> None:
        ScalableTemplate.__init__(self, scale_func)
        AlternatingCornerSquare.__init__(self, dimension, corner_position)

    def to_dict(self) -> dict[str, ty.Any]:
        ret = ScalableTemplate.to_dict(self)
        ret.update(AlternatingCornerSquare.to_dict(self))
        return ret

    def scale_to(self, k: int) -> Template:
        return AlternatingCornerSquare.scale_to(
            self, ScalableTemplate.get_scaled_scale(self, k)
        )
