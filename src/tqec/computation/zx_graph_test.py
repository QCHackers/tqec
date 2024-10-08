import pytest

from tqec.exceptions import TQECException
from tqec.position import Position3D
from tqec.computation.zx_graph import NodeType, ZXEdge, ZXGraph, ZXNode


def test_zx_graph_construction() -> None:
    g = ZXGraph("Test ZX Graph")
    assert g.name == "Test ZX Graph"
    assert len(g.nodes) == 0
    assert len(g.edges) == 0

    node1 = ZXNode(Position3D(0, 0, 0), NodeType.Z)
    g.add_node(node1.position, node1.node_type)
    assert len(g.nodes) == 1
    assert len(g.edges) == 0
    assert g.nodes[0] == node1

    with pytest.raises(TQECException, match="already exists"):
        g.add_node(node1.position, node1.node_type)

    g.add_x_node(Position3D(1, 0, 0))
    g.add_z_node(Position3D(0, 2, 0))
    assert len(g.nodes) == 3
    g.add_edge(Position3D(0, 0, 0), Position3D(1, 0, 0))
    assert len(g.edges) == 1
    with pytest.raises(TQECException, match="Both nodes must exist in the graph."):
        g.add_edge(Position3D(0, 0, 0), Position3D(0, 3, 0))

    with pytest.raises(TQECException, match="An edge must connect two nearby nodes."):
        g.add_edge(Position3D(0, 0, 0), Position3D(0, 2, 0))

    g.add_z_node(Position3D(0, 1, 0))
    g.add_edge(Position3D(0, 0, 0), Position3D(0, 1, 0), has_hadamard=True)
    assert len(g.edges) == 2
    edges = g.edges_at(Position3D(0, 0, 0))
    assert edges[0] == ZXEdge(u=node1, v=ZXNode(Position3D(1, 0, 0), NodeType.X))
    assert edges[1] == ZXEdge(
        u=node1, v=ZXNode(Position3D(0, 1, 0), NodeType.Z), has_hadamard=True
    )
