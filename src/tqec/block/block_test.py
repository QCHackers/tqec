from copy import deepcopy

import pytest

from tqec.block.computation import Computation
from tqec.block.library.closed import zxz_block
from tqec.block.library.open import zxo_block
from tqec.position import Position3D
from tqec.sketchup import BlockGraph, CubeType, PipeType
from tqec.templates.scale import LinearFunction

# TODO implement the CX-gate as computation


def test_cx_gate_computation() -> None:
    assert False


def test_simple_computation() -> None:
    dim = LinearFunction(2, 0)
    zxz = zxz_block(dim)
    computation = Computation(
        blocks={
            Position3D(0, 0, 0): deepcopy(zxz),
            Position3D(0, 0, 1): zxo_block(dim),
            Position3D(0, 0, 2): deepcopy(zxz),
        }
    )
    try:
        computation.to_circuit()
    except Exception as e:
        pytest.fail(f"Failed to convert computation to circuit: {e}")


def test_computation_from_blockgraph() -> None:
    cubes = [
        (Position3D(0, 0, 0), CubeType.ZXZ),
        (Position3D(0, 0, 1), CubeType.ZXZ),
    ]
    pipes = [
        (cubes[0][0], cubes[1][0], PipeType.ZXO),
    ]
    block_graph = BlockGraph(name="Memory Experiment")
    for cube in cubes:
        block_graph.add_cube(*cube)
    block_graph.add_pipe(*pipes[0])
    computation = Computation.from_block_graph(block_graph, LinearFunction(2, 0))
