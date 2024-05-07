import cirq

from tqec.plaquette.library import XXXXMemoryPlaquette, ZZZZMemoryPlaquette
from tqec.templates import RawRectangleTemplate
from tqec.circuit.observable_qubits import observable_qubits_from_template


def test_raw_rectangle_default_observable_qubits():
    template = RawRectangleTemplate(
        [
            [0, 1, 0, 1],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [1, 0, 1, 0],
        ]
    )
    plaquettes = [
        XXXXMemoryPlaquette([1, 2, 3, 4, 5, 6, 7, 8]),
        ZZZZMemoryPlaquette([1, 3, 4, 5, 6, 8]),
    ]
    obs = observable_qubits_from_template(template, plaquettes)
    result = [
        (cirq.GridQubit(3, -1), 0),
        (cirq.GridQubit(3, 1), 0),
        (cirq.GridQubit(3, 3), 0),
        (cirq.GridQubit(3, 5), 0),
        (cirq.GridQubit(3, 7), 0),
    ]
    assert sorted(obs, key=lambda t: t[0].col == result)
