import pytest

from tqec.computation.cube import Cube, ZXBasis, ZXCube
from tqec.computation.pipe import Pipe, PipeKind
from tqec.position import Direction3D, Position3D


def test_pipe_kind() -> None:
    with pytest.raises(Exception, match="Exactly one basis must be None for a pipe."):
        PipeKind(ZXBasis.X, ZXBasis.Z, ZXBasis.X)

    with pytest.raises(Exception, match="Exactly one basis must be None for a pipe."):
        PipeKind(None, None, ZXBasis.X)

    with pytest.raises(Exception, match="Pipe must have different basis walls."):
        PipeKind(None, ZXBasis.X, ZXBasis.X)

    kind = PipeKind.from_str("OXZ")
    assert str(kind) == "OXZ"
    assert kind.direction == Direction3D.X
    assert kind.get_basis_along(Direction3D.X) is None
    assert kind.get_basis_along(Direction3D.Y) == ZXBasis.X
    assert kind.get_basis_along(Direction3D.Z, False) == ZXBasis.Z
    assert kind.is_spatial

    kind = PipeKind.from_str("XZOH")
    assert str(kind) == "XZOH"
    assert kind.direction == Direction3D.Z
    assert kind.is_temporal


def test_pipe() -> None:
    with pytest.raises(
        Exception, match="The pipe must connect two nearby cubes in direction Y."
    ):
        Pipe(
            Cube(Position3D(0, 0, 0), ZXCube.from_str("XXZ")),
            Cube(Position3D(1, 0, 0), ZXCube.from_str("XXZ")),
            PipeKind.from_str("XOZ"),
        )

    pipe = Pipe(
        Cube(Position3D(1, 0, 0), ZXCube.from_str("XXZ")),
        Cube(Position3D(0, 0, 0), ZXCube.from_str("XXZ")),
        PipeKind.from_str("OXZ"),
    )
    assert pipe.direction == Direction3D.X
    assert pipe.u.position < pipe.v.position
    pipe.validate()
    assert list(iter(pipe)) == [pipe.u, pipe.v]


def test_pipe_validate() -> None:
    pipe = Pipe(
        Cube(Position3D(1, 0, 0), ZXCube.from_str("XXZ")),
        Cube(Position3D(0, 0, 0), ZXCube.from_str("XXZ")),
        PipeKind.from_str("OZX"),
    )

    with pytest.raises(
        Exception, match="The pipe has color does not match the cube XXZ"
    ):
        pipe.validate()
