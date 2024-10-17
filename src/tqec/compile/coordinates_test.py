import pytest

from tqec.compile.coordinates import StimCoordinates
from tqec.exceptions import TQECException


def test_creation() -> None:
    with pytest.raises(
        TQECException, match="^Got 0 coordinates but expected at least 3.$"
    ):
        StimCoordinates(tuple())
    with pytest.raises(
        TQECException, match="^Got 1 coordinates but expected at least 3.$"
    ):
        StimCoordinates((0,))
    with pytest.raises(
        TQECException, match="^Got 2 coordinates but expected at least 3.$"
    ):
        StimCoordinates((0, 0))
    StimCoordinates((0, 0, 0))
    StimCoordinates((1, 0, -4))
    StimCoordinates((1.3, 422.92348567, 0.2))
    StimCoordinates(tuple(range(16)))
    with pytest.raises(
        TQECException, match="^Cannot have more than 16 coordinates. Got 17.$"
    ):
        StimCoordinates(tuple(range(17)))


def test_getters() -> None:
    zeros = StimCoordinates((0, 0, 0))
    assert zeros.x == 0
    assert zeros.y == 0
    assert zeros.t == 0
    assert zeros.non_spatial_coordinates == (0,)

    rang = StimCoordinates(tuple(range(12)))
    assert rang.x == 0
    assert rang.y == 1
    assert rang.t == 2
    assert rang.non_spatial_coordinates == tuple(range(2, 12))


def test_offset_spatially_by() -> None:
    coords = StimCoordinates((0, 0, 0)).offset_spatially_by(34, 7)
    assert coords.x == 34
    assert coords.y == 7
    assert coords.t == 0
    assert coords.non_spatial_coordinates == (0,)

    rang = StimCoordinates(tuple(range(12))).offset_spatially_by(-1, 3)
    assert rang.x == -1
    assert rang.y == 4
    assert rang.t == 2
    assert rang.non_spatial_coordinates == tuple(range(2, 12))
