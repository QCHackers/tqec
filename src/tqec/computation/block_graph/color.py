from __future__ import annotations

from dataclasses import astuple, dataclass
from enum import Enum

from tqec.exceptions import TQECException
from tqec.position import Direction3D


class Color(Enum):
    X = "x"
    Z = "z"
    NULL = "o"

    @property
    def is_null(self) -> bool:
        """Check if the color is null."""
        return self == Color.NULL


@dataclass(frozen=True)
class Color3D:
    """Get face colors along the x, y, and z axes."""

    x: Color
    y: Color
    z: Color

    @staticmethod
    def null() -> Color3D:
        """Get the null color."""
        return Color3D(Color.NULL, Color.NULL, Color.NULL)

    @property
    def is_null(self) -> bool:
        """Check if the color is null."""
        return self == Color3D.null()

    def match(self, other: Color3D) -> bool:
        """Check whether the color matches the other color."""
        return all(
            c1.is_null or c2.is_null or c1 == c2
            for c1, c2 in zip(astuple(self), astuple(other))
        )

    def pop_color_at_direction(self, direction: Direction3D) -> Color3D:
        """Replace the color at the given direction with None."""
        return self.push_color_at_direction(direction, Color.NULL)

    def push_color_at_direction(self, direction: Direction3D, color: Color) -> Color3D:
        """Set the color at the given direction."""
        colors = list(astuple(self))
        colors[direction.axis_index] = color
        return Color3D(*colors)

    @staticmethod
    def from_string(s: str, flip_xz: bool = False) -> Color3D:
        s = s.lower()
        if s == "virtual":
            return Color3D.null()
        if len(s) != 3 or any(c not in "xzo" for c in s):
            raise TQECException(
                "s must be a 3-character string containing only 'x', 'z', and 'o'."
            )
        colors: list[Color] = []
        for c in s:
            if c == "o":
                colors.append(Color.NULL)
            elif flip_xz:
                colors.append(Color.Z if c == "x" else Color.X)
            else:
                colors.append(Color(c))
        return Color3D(*colors)
