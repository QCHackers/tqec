from enum import Enum, auto


class CornerPositionEnum(Enum):
    LOWER_LEFT = auto()
    LOWER_RIGHT = auto()
    UPPER_LEFT = auto()
    UPPER_RIGHT = auto()


class TemplateRelativePositionEnum(Enum):
    LEFT_OF = auto()
    RIGHT_OF = auto()
    ABOVE_OF = auto()
    BELOW_OF = auto()


LEFT_OF = TemplateRelativePositionEnum.LEFT_OF
RIGHT_OF = TemplateRelativePositionEnum.RIGHT_OF
ABOVE_OF = TemplateRelativePositionEnum.ABOVE_OF
BELOW_OF = TemplateRelativePositionEnum.BELOW_OF


def opposite_relative_position(
    relative_position: TemplateRelativePositionEnum,
) -> TemplateRelativePositionEnum:
    if relative_position == LEFT_OF:
        return RIGHT_OF
    elif relative_position == RIGHT_OF:
        return LEFT_OF
    elif relative_position == ABOVE_OF:
        return BELOW_OF
    else:  # if relative_position == BELOW_OF:
        return ABOVE_OF
