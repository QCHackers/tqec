from enum import Enum, auto

from tqec.position import Position


class CornerPositionEnum(Enum):
    """Represents a corner.

    Corner positions are stored as coordinates in the coordinate system with:
    - the origin on the upper-left corner
    - the X-axis that goes from the origin to the upper-right corner
    - the Y-axis that goes from the origin to the lower-left corner
    """

    LOWER_LEFT = Position(0, 1)
    LOWER_RIGHT = Position(1, 1)
    UPPER_LEFT = Position(0, 0)
    UPPER_RIGHT = Position(1, 0)


class TemplateRelativePositionEnum(Enum):
    """Represent a relative position between two Template instances.

    Template relative positions are stored as the relative displacement needed to
    encode the position. For example, LEFT_OF is encoded as (-1, 0) as a template
    on the left is one unit backwards on the X-axis.
    """

    LEFT_OF = Position(-1, 0)
    RIGHT_OF = Position(1, 0)
    ABOVE_OF = Position(0, -1)
    BELOW_OF = Position(0, 1)


LEFT_OF = TemplateRelativePositionEnum.LEFT_OF
RIGHT_OF = TemplateRelativePositionEnum.RIGHT_OF
ABOVE_OF = TemplateRelativePositionEnum.ABOVE_OF
BELOW_OF = TemplateRelativePositionEnum.BELOW_OF


class PlaquetteOrientation(Enum):
    RIGHT = auto()
    LEFT = auto()
    DOWN = auto()
    UP = auto()

    def to_plaquette_side(self) -> "PlaquetteSide":
        if self == PlaquetteOrientation.RIGHT:
            return PlaquetteSide.LEFT
        elif self == PlaquetteOrientation.LEFT:
            return PlaquetteSide.RIGHT
        elif self == PlaquetteOrientation.DOWN:
            return PlaquetteSide.UP
        else:  # if self == PlaquetteOrientation.UP:
            return PlaquetteSide.DOWN


class PlaquetteSide(Enum):
    RIGHT = auto()
    LEFT = auto()
    DOWN = auto()
    UP = auto()
