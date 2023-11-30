from dataclasses import dataclass


@dataclass
class Position:
    x: int
    y: int


@dataclass
class Shape2D:
    x: int
    y: int

    def to_numpy_shape(self) -> tuple[int, int]:
        return (self.y, self.x)
