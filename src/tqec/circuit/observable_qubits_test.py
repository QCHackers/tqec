import pytest

from tqec.circuit.observable_qubits import observable_qubits_from_template
from tqec.circuit.qubit import GridQubit
from tqec.circuit.schedule import Schedule
from tqec.plaquette.library import xxxx_memory_plaquette, zzzz_memory_plaquette
from tqec.plaquette.plaquette import Plaquette
from tqec.templates._testing import FixedTemplate


@pytest.fixture
def plaquettes() -> list[Plaquette]:
    return [
        xxxx_memory_plaquette(Schedule.from_offsets([0, 1, 2, 3, 4, 5, 6, 7])),
        zzzz_memory_plaquette(Schedule.from_offsets([0, 2, 3, 4, 5, 7])),
    ]


def test_raw_rectangle_default_observable_qubits(plaquettes: list[Plaquette]) -> None:
    template = FixedTemplate(
        [
            [0, 1, 0, 1],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [1, 0, 1, 0],
        ]
    )

    obs = observable_qubits_from_template(template, plaquettes)
    result = [
        (GridQubit(-1, 3), 0),
        (GridQubit(1, 3), 0),
        (GridQubit(3, 3), 0),
        (GridQubit(5, 3), 0),
        (GridQubit(7, 3), 0),
    ]
    assert sorted(obs, key=lambda t: t[0].x) == result
