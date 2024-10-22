from tqec.computation.cube import Cube, ZXCube
from tqec.computation.zx_graph import ZXGraph, ZXKind
from tqec.position import Position3D


def test_conversion_single_node() -> None:
    zx = ZXGraph("single")
    zx.add_node(Position3D(0, 0, 0), ZXKind.Z)
    block = zx.to_block_graph()
    assert block.num_cubes == 1
    assert block.cubes[0] == Cube(Position3D(0, 0, 0), ZXCube.from_str("ZXX"))

    assert block.to_zx_graph() == zx
