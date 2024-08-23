from tqec.direction import Direction3D

def test_direction_3d() -> None:
    assert Direction3D.X.axis_index == 0
    assert Direction3D.Y.axis_index == 1
    assert Direction3D.Z.axis_index == 2
    assert Direction3D.from_axis_index(0) == Direction3D.X
    assert Direction3D.from_axis_index(1) == Direction3D.Y
    assert Direction3D.from_axis_index(2) == Direction3D.Z
    assert Direction3D.all() == [Direction3D.X, Direction3D.Y, Direction3D.Z]
