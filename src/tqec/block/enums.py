from enum import Enum, auto

from tqec.exceptions import TQECException
from tqec.templates.enums import TemplateSide


class BlockDimension(Enum):
    # TODO: merge with Direction3D from #285
    X = auto()
    Y = auto()
    Z = auto()

    def to_template_sides(self) -> list[TemplateSide]:
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
        else:  # if self == BlockDimension.Z:
            raise TQECException("Cannot get a TemplateSide from the time boundary.")
