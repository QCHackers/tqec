import cirq

from tqec.plaquette.qubit import PlaquetteQubit
from tqec.position import Position


def test_creation() -> None:
    PlaquetteQubit(Position(0, 0))
    PlaquetteQubit(Position(100000, -2398467235))
    PlaquetteQubit(Position(-234897659345, 349578))


def test_to_grid_qubit_origin() -> None:
    pq = PlaquetteQubit(Position(0, 0))
    assert pq.to_grid_qubit() == cirq.GridQubit(0, 0)


def test_to_grid_qubit_non_origin() -> None:
    row, col = 238957462345, -945678
    pq = PlaquetteQubit(Position(col, row))
    assert pq.to_grid_qubit() == cirq.GridQubit(row, col)
