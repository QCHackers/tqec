from tqec.templates.scalable.base import ScalableTemplate
from tqec.templates.shapes.square import AlternatingSquare, AlternatingCornerSquare
from tqec.enums import CornerPositionEnum
import typing as ty


class ScalableAlternatingSquare(ScalableTemplate, AlternatingSquare):
    def __init__(self, dimension: int) -> None:
        ScalableTemplate.__init__(self)
        AlternatingSquare.__init__(self, dimension)

    def to_dict(self) -> dict[str, ty.Any]:
        ret = ScalableTemplate.to_dict(self)
        ret.update(AlternatingSquare.to_dict(self))
        return ret


class ScalableAlternatingCornerSquare(ScalableTemplate, AlternatingCornerSquare):
    def __init__(self, dimension: int, corner_position: CornerPositionEnum) -> None:
        ScalableTemplate.__init__(self)
        AlternatingCornerSquare.__init__(self, dimension, corner_position)

    def to_dict(self) -> dict[str, ty.Any]:
        ret = ScalableTemplate.to_dict(self)
        ret.update(AlternatingCornerSquare.to_dict(self))
        return ret
