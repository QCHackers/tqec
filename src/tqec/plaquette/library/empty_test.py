import stim

from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.empty import empty_rounded_plaquette, empty_square_plaquette
from tqec.plaquette.qubit import RoundedPlaquetteQubits, SquarePlaquetteQubits


def test_empty_plaquettes() -> None:
    empty_square = empty_square_plaquette()
    assert empty_square.qubits == SquarePlaquetteQubits()
    assert len(empty_square.circuit.schedule) == 0
    assert empty_square.circuit.get_circuit == stim.Circuit()
    for orientation in PlaquetteOrientation:
        empty_rounded = empty_rounded_plaquette(orientation)
        assert empty_rounded.qubits == RoundedPlaquetteQubits(orientation)
        assert len(empty_rounded.circuit.schedule) == 0
        assert empty_rounded.circuit.get_circuit == stim.Circuit()
