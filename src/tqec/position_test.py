import pytest

from tqec.exceptions import TQECException
from tqec.position import Direction3D, Position2D, Position3D, Shape2D


def test_position() -> None:
    pos = Position2D(1, 3)
    assert pos.x == 1
    assert pos.y == 3


def test_shape() -> None:
    shape = Shape2D(2, 5)
    assert shape.x == 2
    assert shape.y == 5
    assert shape.to_numpy_shape() == (5, 2)


def test_position_3d() -> None:
    p1 = Position3D(0, 0, 0)
    assert p1.as_tuple() == (0, 0, 0)
    assert p1.shift_by(1, 2, 3) == Position3D(1, 2, 3)
    assert p1.is_neighbour(Position3D(0, 0, 1))
    assert p1.is_neighbour(Position3D(0, 1, 0))
    assert p1.is_neighbour(Position3D(-1, 0, 0))
    assert not p1.is_neighbour(Position3D(1, 0, 1))
    assert not p1.is_neighbour(Position3D(0, -1, 1))
    with pytest.raises(TQECException, match="Position must be an integer"):
        Position3D(0.5, 0, 0)  # type: ignore[arg-type]


def test_direction_3d() -> None:
    assert Direction3D.X.axis_index == 0
    assert Direction3D.Y.axis_index == 1
    assert Direction3D.Z.axis_index == 2
    assert Direction3D.from_axis_index(0) == Direction3D.X
    assert Direction3D.from_axis_index(1) == Direction3D.Y
    assert Direction3D.from_axis_index(2) == Direction3D.Z
    assert Direction3D.all() == [Direction3D.X, Direction3D.Y, Direction3D.Z]
