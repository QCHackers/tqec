import pytest

from tqec.exceptions import TQECException
from tqec.sketchup.zx_graph import Position3D, ZXGraph
from tqec.sketchup.block_graph import BlockGraph, CubeType, PipeType
from tqec.templates.scale import LinearFunction


def test_block_graph_construction() -> None:
    g = BlockGraph("Test Block Graph")
    assert g.name == "Test Block Graph"
    assert len(g.cubes) == 0
    assert len(g.pipes) == 0

    g.add_cube(Position3D(0, 0, 0), CubeType.ZXZ)
    assert len(g.cubes) == 1
    assert len(g.pipes) == 0
    assert g.cubes[0].position == Position3D(0, 0, 0)
    assert g.cubes[0].cube_type == CubeType.ZXZ

    g.add_cube(Position3D(1, 0, 0), CubeType.XXZ)
    g.add_pipe(Position3D(0, 0, 0), Position3D(1, 0, 0), PipeType.OXZ)
    g.add_cube(Position3D(2, 0, 0), CubeType.XXZ)
    assert len(g.cubes) == 3
    assert len(g.pipes) == 1

    with pytest.raises(TQECException, match="already exists in the graph."):
        g.add_cube(Position3D(0, 0, 0), CubeType.XXZ)

    with pytest.raises(TQECException, match="Both cubes must exist in the graph."):
        g.add_pipe(Position3D(0, 0, 0), Position3D(0, 1, 0), PipeType.OXZ)

    with pytest.raises(TQECException, match="A pipe must connect two nearby cubes."):
        g.add_pipe(Position3D(0, 0, 0), Position3D(2, 0, 0), PipeType.OXZ)


def test_validity_constraints_3d_corner() -> None:
    g = BlockGraph("Test Block Graph")
    g.add_cube(Position3D(0, 0, 0), CubeType.ZXZ)
    for position, pipe_type in [
        (Position3D(1, 0, 0), PipeType.OXZ),
        (Position3D(0, 1, 0), PipeType.ZOX),
        (Position3D(0, 0, 1), PipeType.ZXO),
    ]:
        g.add_cube(position, CubeType.VIRTUAL)
        g.add_pipe(Position3D(0, 0, 0), position, pipe_type)
    with pytest.raises(TQECException, match="has a 3D corner."):
        g.check_validity()


def test_validity_passthrough_color_match() -> None:
    g = BlockGraph("Test Block Graph")
    g.add_cube(Position3D(0, 0, 0), CubeType.ZXZ)
    g.add_cube(Position3D(1, 0, 0), CubeType.VIRTUAL)
    g.add_cube(Position3D(0, 0, 1), CubeType.XZX)

    g.add_pipe(Position3D(0, 0, 0), Position3D(0, 0, 1), PipeType.ZXOH)
    g.check_validity()

    g.add_pipe(Position3D(0, 0, 0), Position3D(1, 0, 0), PipeType.OZX)
    with pytest.raises(TQECException, match="has unmatched color at pass-through"):
        g.check_validity()


def test_validity_at_turn_color_match() -> None:
    g = BlockGraph("Test Block Graph")
    g.add_cube(Position3D(0, 0, 0), CubeType.ZXZ)
    g.add_cube(Position3D(1, 0, 0), CubeType.XXZ)
    g.add_cube(Position3D(0, 0, 1), CubeType.XZX)

    g.add_pipe(Position3D(0, 0, 0), Position3D(1, 0, 0), PipeType.OXZ)
    g.add_pipe(Position3D(0, 0, 0), Position3D(0, 0, 1), PipeType.ZXOH)
    g.check_validity()


def test_convert_zx_graph_no_corner() -> None:
    # Cannot resolve the orientation of a simple idle
    g = ZXGraph("Test ZX Graph Idle")
    g.add_z_node(Position3D(0, 0, 0))
    g.add_z_node(Position3D(0, 0, 1))
    g.add_edge(Position3D(0, 0, 0), Position3D(0, 0, 1))
    with pytest.raises(TQECException, match="There should be at least one corner node"):
        g.to_block_graph()


def test_convert_zx_graph_roundtrip() -> None:
    g = ZXGraph("Test ZX Graph")
    g.add_virtual_node(Position3D(0, 0, 0))
    g.add_x_node(Position3D(0, 0, 1))
    g.add_z_node(Position3D(0, 0, 2))
    g.add_virtual_node(Position3D(1, 0, 0))
    g.add_x_node(Position3D(1, 0, 1))
    g.add_z_node(Position3D(1, 0, 2))
    g.add_edge(Position3D(0, 0, 0), Position3D(0, 0, 1))
    g.add_edge(Position3D(0, 0, 1), Position3D(0, 0, 2), has_hadamard=True)
    g.add_edge(Position3D(0, 0, 1), Position3D(1, 0, 1))
    g.add_edge(Position3D(1, 0, 0), Position3D(1, 0, 1))
    g.add_edge(Position3D(1, 0, 1), Position3D(1, 0, 2))
    block_graph = g.to_block_graph()
    g2 = block_graph.to_zx_graph()
    assert g2 == g
    assert g2.to_block_graph() == block_graph


def test_circuit_from_blockgraph() -> None:
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
    circuit = block_graph.to_circuit(LinearFunction(2, 0))
    assert circuit is not None


def test_circuit_from_cx_blockgraph() -> None:
    block_graph = BlockGraph("Logical CNOT Block Graph")
    for position, cube_type in [
        (Position3D(0, 0, 0), CubeType.ZXZ),
        (Position3D(0, 0, 1), CubeType.ZXX),
        (Position3D(0, 0, 2), CubeType.ZXZ),
        (Position3D(0, 1, 1), CubeType.ZXX),
        (Position3D(0, 1, 2), CubeType.ZXZ),
        (Position3D(1, 1, 0), CubeType.ZXZ),
        (Position3D(1, 1, 1), CubeType.ZXZ),
        (Position3D(1, 1, 2), CubeType.ZXZ),
    ]:
        block_graph.add_cube(position, cube_type)

    for u, v, pipe_type in [
        (Position3D(0, 0, 0), Position3D(0, 0, 1), PipeType.ZXO),
        (Position3D(0, 0, 1), Position3D(0, 0, 2), PipeType.ZXO),
        (Position3D(0, 0, 1), Position3D(0, 1, 1), PipeType.ZOX),
        (Position3D(0, 1, 1), Position3D(0, 1, 2), PipeType.ZXO),
        (Position3D(0, 1, 2), Position3D(1, 1, 2), PipeType.OXZ),
        (Position3D(1, 1, 0), Position3D(1, 1, 1), PipeType.ZXO),
        (Position3D(1, 1, 1), Position3D(1, 1, 2), PipeType.ZXO),
    ]:
        block_graph.add_pipe(u, v, pipe_type)
    circuit = block_graph.to_circuit(LinearFunction(2, 0))
    assert circuit is not None
