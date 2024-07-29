from enum import Enum, auto

from tqec.exceptions import TQECException
from tqec.templates.enums import TemplateSide


class BlockDimension(Enum):
    X = auto()
    Y = auto()
    Z = auto()
    T = Z

    def to_template_sides(self) -> list[TemplateSide]:
        if self == BlockDimension.Z or self == BlockDimension.T:
            raise TQECException("Cannot get a TemplateSide from the time boundary.")
        if self == BlockDimension.X:
            return [
                TemplateSide.TOP_LEFT,
                TemplateSide.LEFT,
                TemplateSide.BOTTOM_LEFT,
                TemplateSide.TOP_RIGHT,
                TemplateSide.RIGHT,
                TemplateSide.BOTTOM_RIGHT,
            ]
        elif self == BlockDimension.Y:
            return [
                TemplateSide.TOP_LEFT,
                TemplateSide.TOP,
                TemplateSide.TOP_RIGHT,
                TemplateSide.BOTTOM_LEFT,
                TemplateSide.BOTTOM,
                TemplateSide.BOTTOM_RIGHT,
            ]
        else:
            raise TQECException(f"Unknown BlockDimension: {self}.")
