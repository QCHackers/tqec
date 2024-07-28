from tqec.position import Position, Shape2D


def test_position() -> None:
    pos = Position(1, 3)
    assert pos.x == 1
    assert pos.y == 3


def test_shape() -> None:
    shape = Shape2D(2, 5)
    assert shape.x == 2
    assert shape.y == 5
    assert shape.to_numpy_shape() == (5, 2)
