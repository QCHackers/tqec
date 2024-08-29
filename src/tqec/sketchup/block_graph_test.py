import pytest

from tqec.sketchup.zx_graph import Position3D, ZXGraph
from tqec.sketchup.block_graph import BlockGraph, CubeType, PipeType
from tqec.exceptions import TQECException


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
    g = ZXGraph("Test ZX Graph Idle")
    g.add_z_node(Position3D(0, 0, 0))
    g.add_z_node(Position3D(0, 0, 1))
    g.add_edge(Position3D(0, 0, 0), Position3D(0, 0, 1))
    bg = g.to_block_graph()
    c1 = bg.get_cube(Position3D(0, 0, 0))
    assert c1 is not None
    assert c1.cube_type == CubeType.XZZ
    c2 = bg.get_cube(Position3D(0, 0, 1))
    assert c2 is not None
    assert c2.cube_type == CubeType.XZZ

    g2 = ZXGraph("Horizontal line")
    g2.add_z_node(Position3D(0, 0, 0))
    g2.add_x_node(Position3D(1, 0, 0))
    g2.add_edge(Position3D(0, 0, 0), Position3D(1, 0, 0), has_hadamard=True)
    bg2 = g2.to_block_graph()
    c3 = bg2.get_cube(Position3D(0, 0, 0))
    assert c3 is not None
    assert c3.cube_type == CubeType.ZXZ
    c4 = bg2.get_cube(Position3D(1, 0, 0))
    assert c4 is not None
    assert c4.cube_type == CubeType.XZX


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
