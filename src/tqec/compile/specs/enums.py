from enum import Flag, auto


class JunctionArms(Flag):
    NONE = 0
    UP = auto()
    RIGHT = auto()
    DOWN = auto()
    LEFT = auto()

    @classmethod
    def get_map_from_arm_to_shift(cls) -> dict["JunctionArms", tuple[int, int]]:
        return {
            cls.UP: (0, 1),
            cls.RIGHT: (1, 0),
            cls.DOWN: (0, -1),
            cls.LEFT: (-1, 0),
        }
