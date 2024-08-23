from copy import deepcopy

import pytest

from tqec.block.block import Computation, Position3D
from tqec.block.library.closed import zxz_block
from tqec.block.library.open import zxo_block
from tqec.templates.scale import LinearFunction

# TODO implement the CX-gate as computation


def test_cx_gate_computation() -> None:
    assert False


def test_simple_computation() -> None:
    dim = LinearFunction(2, 0)
    zxz = zxz_block(dim)
    computation = Computation(
        {
            Position3D(0, 0, 0): deepcopy(zxz),
            Position3D(0, 0, 1): zxo_block(dim),
            Position3D(0, 0, 2): deepcopy(zxz),
        }
    )
    try:
        computation.to_circuit()
    except Exception as e:
        pytest.fail(f"Failed to convert computation to circuit: {e}")
