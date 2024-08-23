from enum import Enum

from tqec.exceptions import TQECException
from tqec.templates.enums import TemplateSide


class Direction3D(Enum):
    """Axis directions in the 3D spacetime diagram."""

    X = 0
    Y = 1
    Z = 2

    @staticmethod
    def all() -> list["Direction3D"]:
        """Get all directions."""
        return list(Direction3D)

    @staticmethod
    def from_axis_index(i: int) -> "Direction3D":
        """Get the direction from the axis index."""
        if i not in [d.value for d in Direction3D]:
            raise TQECException(f"Invalid axis index: {i}")
        return Direction3D.all()[i]

    @property
    def axis_index(self) -> int:
        """Get the axis index."""
        return self.value

    def __str__(self) -> str:
        return self.name

    def to_template_sides(self) -> list[TemplateSide]:
        """Convert the direction to the corresponding template sides.

        Raises:
            TQECException: It the temporal direction is requested.

        Returns:
            list[TemplateSide]: The template sides corresponding to the direction.
        """
        if self == Direction3D.X:
            return [
                TemplateSide.TOP_LEFT,
                TemplateSide.LEFT,
                TemplateSide.BOTTOM_LEFT,
                TemplateSide.TOP_RIGHT,
                TemplateSide.RIGHT,
                TemplateSide.BOTTOM_RIGHT,
            ]
        if self == Direction3D.Y:
            return [
                TemplateSide.TOP_LEFT,
                TemplateSide.TOP,
                TemplateSide.TOP_RIGHT,
                TemplateSide.BOTTOM_LEFT,
                TemplateSide.BOTTOM,
                TemplateSide.BOTTOM_RIGHT,
            ]
        raise TQECException("Cannot get a TemplateSide from the time boundary.")
