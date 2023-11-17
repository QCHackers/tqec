from tqec.templates.scalable.base import ScalableTemplate
from tqec.templates.shapes.square import AlternatingSquare, AlternatingCornerSquare
from tqec.enums import CornerPositionEnum


class ScalableAlternatingSquare(ScalableTemplate, AlternatingSquare):
    def __init__(self, dimension: int) -> None:
        ScalableTemplate.__init__(self)
        AlternatingSquare.__init__(self, dimension)


class ScalableAlternatingCornerSquare(ScalableTemplate, AlternatingCornerSquare):
    def __init__(self, dimension: int, corner_position: CornerPositionEnum) -> None:
        ScalableTemplate.__init__(self)
        AlternatingCornerSquare.__init__(self, dimension, corner_position)
