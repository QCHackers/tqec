import cirq
import pytest

from tqec.circuit.circuit import generate_circuit
from tqec.exceptions import TQECException
from tqec.plaquette.library import ZSquareInitialisationPlaquette
from tqec.plaquette.plaquette import Plaquette
from tqec.templates.atomic.rectangle import RawRectangleTemplate
from tqec.templates.base import Template


@pytest.fixture
def initialisation_plaquette() -> Plaquette:
    return ZSquareInitialisationPlaquette()


@pytest.fixture
def one_by_one_template() -> Template:
    return RawRectangleTemplate([[0]])


def test_generate_initialisation_circuit_list(
    initialisation_plaquette: Plaquette, one_by_one_template
):
    circuit = generate_circuit(one_by_one_template, [initialisation_plaquette])
    assert circuit == cirq.Circuit(
        cirq.R(q.to_grid_qubit()) for q in initialisation_plaquette.qubits
    )


def test_generate_initialisation_circuit_dict(
    initialisation_plaquette: Plaquette, one_by_one_template
):
    circuit = generate_circuit(one_by_one_template, {1: initialisation_plaquette})
    assert circuit == cirq.Circuit(
        cirq.R(q.to_grid_qubit()) for q in initialisation_plaquette.qubits
    )


def test_generate_initialisation_circuit_dict_0_indexed(
    initialisation_plaquette: Plaquette, one_by_one_template
):
    with pytest.raises(TQECException):
        generate_circuit(one_by_one_template, {0: initialisation_plaquette})


def test_generate_circuit_wrong_number_of_plaquettes(
    initialisation_plaquette: Plaquette, one_by_one_template
):
    with pytest.raises(TQECException):
        generate_circuit(
            one_by_one_template, [initialisation_plaquette, initialisation_plaquette]
        )
    with pytest.raises(TQECException):
        generate_circuit(one_by_one_template, [])
