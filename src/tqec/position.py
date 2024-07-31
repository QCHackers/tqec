from dataclasses import dataclass


@dataclass(frozen=True)
class Position2D:
    """Simple wrapper around tuple[int, int].

    This class is here to explicitly name the type of variables as positions
    instead of having a tuple[int, int] that could be:
    - a position,
    - a shape,
    - coefficients for positions,
    - displacements.
    """

    x: int
    y: int

    def to_grid_qubit(self) -> tuple[int, int]:
        """Returns the position as a tuple following the cirq.GridQubit coordinate system."""
        return (self.y, self.x)


@dataclass
class Shape2D:
    """Simple wrapper around tuple[int, int].

    This class is here to explicitly name the type of variables as shapes
    instead of having a tuple[int, int] that could be:
    - a position,
    - a shape,
    - coefficients for positions,
    - displacements.
    """

    x: int
    y: int

    def to_numpy_shape(self) -> tuple[int, int]:
        """Returns the shape according to numpy indexing.

        In the coordinate system used in this library, numpy indexes arrays
        using (y, x) coordinates. This method is here to translate a Shape
        instance to a numpy shape transparently for the user.
        """
        return (self.y, self.x)


@dataclass
class Displacement:
    """Simple wrapper around tuple[int, int].

    This class is here to explicitely name the type of variables as displacements
    instead of having a tuple[int, int] that could be:
    - a position,
    - a shape,
    - coefficients for positions,
    - displacements.
    """

    x: int
    y: int


@dataclass(frozen=True)
class Position3D:
    x: int
    y: int
    z: int

    @property
    def spatial_coordinates(self) -> Position2D:
        return Position2D(self.x, self.y)
