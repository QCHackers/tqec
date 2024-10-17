from __future__ import annotations

from dataclasses import dataclass

from tqec.exceptions import TQECException
from tqec.position import Position2D
from tqec.scale import round_or_fail


@dataclass(frozen=True)
class StimCoordinates:
    coordinates: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.coordinates) < 3:
            raise TQECException(
                f"Got {len(self.coordinates)} coordinates but expected at least 3."
            )
        if len(self.coordinates) > 16:
            raise TQECException(
                f"Cannot have more than 16 coordinates. Got {len(self.coordinates)}."
            )

    @property
    def x(self) -> float:
        return self.coordinates[0]

    @property
    def y(self) -> float:
        return self.coordinates[1]

    @property
    def spatial(self) -> Position2D:
        return Position2D(round_or_fail(self.x), round_or_fail(self.y))

    @property
    def t(self) -> float:
        return self.coordinates[2]

    def to_stim_coordinates(self) -> tuple[float, ...]:
        return self.coordinates

    def __str__(self) -> str:
        return "(" + ",".join(f"{c:.2f}" for c in self.coordinates) + ")"

    @property
    def non_spatial_coordinates(self) -> tuple[float, ...]:
        return self.coordinates[2:]

    def offset_spatially_by(self, x: float, y: float) -> StimCoordinates:
        return StimCoordinates((self.x + x, self.y + y, *self.non_spatial_coordinates))
