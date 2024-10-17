from tqec.circuit.coordinates import StimCoordinates


def test_creation() -> None:
    StimCoordinates(0, 0, 0)
    StimCoordinates(1, 0, -4)
    StimCoordinates(1.3, 422.92348567, 0.2)


def test_getters() -> None:
    zeros = StimCoordinates(0, 0, 0)
    assert zeros.x == 0
    assert zeros.y == 0
    assert zeros.t == 0

    coords = StimCoordinates(-1, 34, 12)
    assert coords.x == -1
    assert coords.y == 34
    assert coords.t == 12


def test_offset_spatially_by() -> None:
    coords = StimCoordinates(0, 0, 0).offset_spatially_by(34, 7)
    assert coords.x == 34
    assert coords.y == 7
    assert coords.t == 0
