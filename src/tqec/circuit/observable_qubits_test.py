import cirq
import pytest

from tqec.circuit.observable_qubits import observable_qubits_from_template
from tqec.plaquette.library import xxxx_memory_plaquette, zzzz_memory_plaquette
from tqec.plaquette.plaquette import Plaquette
from tqec.templates import RawRectangleTemplate


@pytest.fixture
def plaquettes() -> list[Plaquette]:
    return [
        xxxx_memory_plaquette([1, 2, 3, 4, 5, 6, 7, 8]),
        zzzz_memory_plaquette([1, 3, 4, 5, 6, 8]),
    ]


def test_raw_rectangle_default_obserevable_qubits(plaquettes: list[Plaquette]):
    template = RawRectangleTemplate(
        [
            [0, 1, 0, 1],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [1, 0, 1, 0],
        ]
    )

    obs = observable_qubits_from_template(template, plaquettes)
    result = [
        (cirq.GridQubit(3, -1), 0),
        (cirq.GridQubit(3, 1), 0),
        (cirq.GridQubit(3, 3), 0),
        (cirq.GridQubit(3, 5), 0),
        (cirq.GridQubit(3, 7), 0),
    ]
    assert sorted(obs, key=lambda t: t[0].col) == result
