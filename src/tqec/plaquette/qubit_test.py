from copy import deepcopy

import cirq
import pytest

from tqec.plaquette.enums import PlaquetteOrientation, PlaquetteSide
from tqec.plaquette.qubit import (
    PlaquetteQubit,
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)
from tqec.position import Position
from tqec.templates.enums import TemplateOrientation


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


def test_square_plaquette_qubits() -> None:
    qubits = SquarePlaquetteQubits()
    top_left = PlaquetteQubit(Position(-1, -1))
    top_right = PlaquetteQubit(Position(1, -1))
    bot_left = PlaquetteQubit(Position(-1, 1))
    bot_right = PlaquetteQubit(Position(1, 1))
    center = PlaquetteQubit(Position(0, 0))
    assert set(qubits.data_qubits) == {top_left, top_right, bot_left, bot_right}
    assert set(qubits.syndrome_qubits) == {center}
    assert set(qubits.get_qubits_on_side(PlaquetteSide.LEFT)) == {top_left, bot_left}
    assert set(qubits.get_qubits_on_side(PlaquetteSide.RIGHT)) == {top_right, bot_right}
    assert set(qubits.get_qubits_on_side(PlaquetteSide.UP)) == {top_left, top_right}
    assert set(qubits.get_qubits_on_side(PlaquetteSide.DOWN)) == {bot_left, bot_right}
    assert set(qubits.get_edge_qubits(TemplateOrientation.HORIZONTAL)) == {
        bot_left,
        bot_right,
    }
    assert set(qubits.get_edge_qubits(TemplateOrientation.VERTICAL)) == {
        top_right,
        bot_right,
    }

    before_permutation = deepcopy(qubits.data_qubits)
    permutation = [0, 2, 1, 3]
    qubits = qubits.permute_data_qubits([0, 2, 1, 3])
    assert set(qubits.data_qubits) == {top_left, top_right, bot_left, bot_right}
    assert qubits.data_qubits == [before_permutation[i] for i in permutation]
    assert set(qubits.syndrome_qubits) == {center}

    with pytest.raises(IndexError):
        qubits.permute_data_qubits([1, 2, 3, 4])


def test_rounded_plaquette_qubits() -> None:
    qubits = RoundedPlaquetteQubits(PlaquetteOrientation.UP)
    bot_left = PlaquetteQubit(Position(-1, 1))
    bot_right = PlaquetteQubit(Position(1, 1))
    center = PlaquetteQubit(Position(0, 0))
    assert set(qubits.data_qubits) == {bot_left, bot_right}
    assert set(qubits.syndrome_qubits) == {center}
    assert set(qubits.get_qubits_on_side(PlaquetteSide.LEFT)) == {bot_left}
    assert set(qubits.get_qubits_on_side(PlaquetteSide.RIGHT)) == {bot_right}
    assert set(qubits.get_qubits_on_side(PlaquetteSide.UP)) == {center}
    assert set(qubits.get_qubits_on_side(PlaquetteSide.DOWN)) == {bot_left, bot_right}
    assert set(qubits.get_edge_qubits(TemplateOrientation.HORIZONTAL)) == {
        bot_left,
        bot_right,
    }
    assert set(qubits.get_edge_qubits(TemplateOrientation.VERTICAL)) == {bot_right}
