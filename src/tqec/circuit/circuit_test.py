from collections import defaultdict

import cirq
import pytest

from tqec.circuit.circuit import generate_circuit
from tqec.exceptions import TQECException
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library import zz_memory_plaquette
from tqec.plaquette.plaquette import Plaquette, Plaquettes
from tqec.plaquette.qubit import PlaquetteQubits
from tqec.templates._testing import FixedTemplate
from tqec.templates.base import Template


@pytest.fixture
def plaquette() -> Plaquette:
    return zz_memory_plaquette(PlaquetteOrientation.LEFT, [1, 5, 6, 8])


@pytest.fixture
def one_by_one_template() -> Template:
    return FixedTemplate([[0]])


def _expected_circuit(qubits: PlaquetteQubits) -> cirq.Circuit:
    (syndrome_qubit,) = qubits.get_syndrome_qubits_cirq()
    return cirq.Circuit(
        cirq.Moment(cirq.R(syndrome_qubit).with_tags(Plaquette.get_mergeable_tag())),
        cirq.Moment(cirq.CNOT(qubits.data_qubits[0].to_grid_qubit(), syndrome_qubit)),
        cirq.Moment(cirq.CNOT(qubits.data_qubits[1].to_grid_qubit(), syndrome_qubit)),
        cirq.Moment(cirq.M(syndrome_qubit).with_tags(Plaquette.get_mergeable_tag())),
    )


def test_generate_circuit_dict(
    plaquette: Plaquette, one_by_one_template: Template
) -> None:
    circuit = generate_circuit(one_by_one_template, Plaquettes({1: plaquette}))
    assert circuit == _expected_circuit(plaquette.qubits)


def test_generate_circuit_defaultdict(
    plaquette: Plaquette, one_by_one_template: Template
) -> None:
    circuit = generate_circuit(
        one_by_one_template, Plaquettes(defaultdict(lambda: plaquette))
    )
    assert circuit == _expected_circuit(plaquette.qubits)


def test_generate_circuit_dict_0_indexed(
    plaquette: Plaquette, one_by_one_template: Template
) -> None:
    with pytest.raises(TQECException):
        generate_circuit(one_by_one_template, Plaquettes({0: plaquette}))


def test_generate_circuit_wrong_number_of_plaquettes(
    plaquette: Plaquette, one_by_one_template: Template
) -> None:
    with pytest.raises(TQECException):
        generate_circuit(one_by_one_template, Plaquettes({1: plaquette, 2: plaquette}))
    with pytest.raises(TQECException):
        generate_circuit(one_by_one_template, Plaquettes({}))
