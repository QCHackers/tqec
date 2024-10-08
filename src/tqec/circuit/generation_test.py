from collections import defaultdict

import pytest
import stim

from tqec.circuit.generation import generate_circuit
from tqec.exceptions import TQECException
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library import make_css_surface_code_plaquette
from tqec.plaquette.plaquette import Plaquette, Plaquettes
from tqec.templates._testing import FixedTemplate
from tqec.templates.base import Template


@pytest.fixture
def plaquette() -> Plaquette:
    return make_css_surface_code_plaquette("Z").project_on_boundary(
        PlaquetteOrientation.LEFT
    )


@pytest.fixture
def one_by_one_template() -> Template:
    return FixedTemplate([[0]])


def _expected_circuit() -> stim.Circuit:
    return stim.Circuit("""
    QUBIT_COORDS(0, 0) 0
    QUBIT_COORDS(1, -1) 1
    QUBIT_COORDS(1, 1) 2
    R 0
    TICK
    TICK
    TICK
    CX 1 0
    TICK
    CX 2 0
    TICK
    M 0
""")


def test_generate_circuit_dict(
    plaquette: Plaquette, one_by_one_template: Template
) -> None:
    circuit = generate_circuit(one_by_one_template, Plaquettes({1: plaquette}))
    assert circuit.get_circuit() == _expected_circuit()


def test_generate_circuit_defaultdict(
    plaquette: Plaquette, one_by_one_template: Template
) -> None:
    circuit = generate_circuit(
        one_by_one_template, Plaquettes(defaultdict(lambda: plaquette))
    )
    assert circuit.get_circuit() == _expected_circuit()


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
