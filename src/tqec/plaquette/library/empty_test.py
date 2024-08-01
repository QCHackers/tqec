import cirq

from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.empty import empty_rounded_plaquette, empty_square_plaquette
from tqec.plaquette.qubit import RoundedPlaquetteQubits, SquarePlaquetteQubits


def test_empty_plaquettes():
    empty_square = empty_square_plaquette()
    assert empty_square.qubits == SquarePlaquetteQubits()
    assert empty_square.circuit.schedule == []
    assert empty_square.circuit.raw_circuit == cirq.Circuit()
    for orientation in PlaquetteOrientation:
        empty_rounded = empty_rounded_plaquette(orientation)
        assert empty_rounded.qubits == RoundedPlaquetteQubits(orientation)
        assert empty_rounded.circuit.schedule == []
        assert empty_rounded.circuit.raw_circuit == cirq.Circuit()
