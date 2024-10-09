import stim

from tqec.circuit.qubit import GridQubit
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.empty import empty_square_plaquette
from tqec.plaquette.qubit import PlaquetteQubits, SquarePlaquetteQubits


def test_empty_plaquettes() -> None:
    empty_square = empty_square_plaquette()
    assert empty_square.qubits == SquarePlaquetteQubits()
    assert len(empty_square.circuit.schedule) == 0
    assert empty_square.circuit.get_circuit() == stim.Circuit()
    empty_up = empty_square.project_on_boundary(PlaquetteOrientation.UP)
    assert empty_up.qubits == PlaquetteQubits(
        data_qubits=[GridQubit(-1, 1), GridQubit(1, 1)],
        syndrome_qubits=[GridQubit(0, 0)],
    )
