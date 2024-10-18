from tqec.computation.block_graph.graph import BlockGraph
from tqec.computation.zx_graph import ZXGraph, NodeType
from tqec.position import Position3D


def three_cnot_zx_graph() -> ZXGraph:
    zx_graph = ZXGraph("Three CNOT")
    nodes = [
        (Position3D(0, 0, 0), NodeType.X),
        (Position3D(0, 1, 0), NodeType.X),
        (Position3D(1, 0, 0), NodeType.Z),
        (Position3D(1, 0, 1), NodeType.X),
        (Position3D(1, 1, 0), NodeType.Z),
        (Position3D(1, 1, 1), NodeType.X),
        (Position3D(-1, 0, 0), NodeType.V),
        (Position3D(0, -1, 0), NodeType.V),
        (Position3D(1, 0, -1), NodeType.V),
        (Position3D(1, 0, 2), NodeType.V),
        (Position3D(1, 1, -1), NodeType.V),
        (Position3D(2, 1, 0), NodeType.V),
    ]
    for node in nodes:
        zx_graph.add_node(node[0], node[1])

    zx_graph.add_edge(Position3D(-1, 0, 0), Position3D(0, 0, 0))
    zx_graph.add_edge(Position3D(0, -1, 0), Position3D(0, 0, 0))
    zx_graph.add_edge(Position3D(1, 0, 0), Position3D(0, 0, 0))
    zx_graph.add_edge(Position3D(1, 0, 0), Position3D(1, 0, -1))
    zx_graph.add_edge(Position3D(1, 0, 0), Position3D(1, 0, 1))
    zx_graph.add_edge(Position3D(1, 1, 1), Position3D(1, 0, 1))
    zx_graph.add_edge(Position3D(1, 0, 2), Position3D(1, 0, 1))
    zx_graph.add_edge(Position3D(0, 1, 0), Position3D(0, 0, 0))
    zx_graph.add_edge(Position3D(0, 1, 0), Position3D(1, 1, 0))
    zx_graph.add_edge(Position3D(1, 1, 1), Position3D(1, 1, 0))
    zx_graph.add_edge(Position3D(1, 1, -1), Position3D(1, 1, 0))
    zx_graph.add_edge(Position3D(2, 1, 0), Position3D(1, 1, 0))
    return zx_graph


def three_cnot_block_graph() -> BlockGraph:
    zx_graph = three_cnot_zx_graph()
    return zx_graph.to_block_graph("Three CNOT")
