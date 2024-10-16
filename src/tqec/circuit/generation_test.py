from collections import defaultdict

import pytest
import stim

from tqec.circuit.generation import generate_circuit
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.frozendefaultdict import FrozenDefaultDict
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
    CX 1 0
    TICK
    TICK
    CX 2 0
    TICK
    M 0
""")


def test_generate_circuit_defaultdict(
    plaquette: Plaquette, one_by_one_template: Template
) -> None:
    circuit = generate_circuit(
        one_by_one_template,
        2,
        Plaquettes(FrozenDefaultDict(default_factory=lambda: plaquette)),
    )
    assert circuit.get_circuit() == _expected_circuit()
