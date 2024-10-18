import pytest

from tqec.exceptions import TQECException
from tqec.position import Direction3D, Position3D
from tqec.computation.zx_graph import NodeType, ZXEdge, ZXGraph, ZXNode
from tqec.gallery.logical_cnot import logical_cnot_zx_graph


def test_zx_node() -> None:
    node = ZXNode(Position3D(0, 0, 0), NodeType.Z, "test")
    assert not node.is_port

    node = ZXNode(Position3D(0, 1, 4), NodeType.P, "input")
    assert node.is_port


def test_zx_edge() -> None:
    edge = ZXEdge(
        ZXNode(Position3D(2, 0, 0), NodeType.Y),
        ZXNode(Position3D(1, 0, 0), NodeType.X),
    )
    assert edge.u.position == Position3D(1, 0, 0)
    assert edge.v.position == Position3D(2, 0, 0)
    assert edge.direction == Direction3D.X

    with pytest.raises(TQECException, match="An edge must connect two nearby nodes."):
        ZXEdge(
            ZXNode(Position3D(0, 0, 0), NodeType.Y),
            ZXNode(Position3D(2, 0, 0), NodeType.X),
        )

    with pytest.raises(TQECException, match="Cannot create an edge between two ports."):
        ZXEdge(
            ZXNode(Position3D(0, 0, 0), NodeType.P),
            ZXNode(Position3D(1, 0, 0), NodeType.P),
        )


def test_zx_graph_construction() -> None:
    g = ZXGraph("Test ZX Graph")
    assert g.name == "Test ZX Graph"
    assert len(g.nodes) == 0
    assert len(g.edges) == 0


def test_zx_graph_add_node() -> None:
    g = ZXGraph()
    g.add_node(Position3D(0, 0, 0), NodeType.Z)
    assert g.num_nodes == 1
    assert g[Position3D(0, 0, 0)].node_type == NodeType.Z
    assert Position3D(0, 0, 0) in g

    g.add_y_node(Position3D(0, 1, 1))
    assert g.num_nodes == 2

    with pytest.raises(TQECException, match="A port cannot be added solely"):
        g.add_node(Position3D(2, 0, 0), NodeType.P)

    with pytest.raises(TQECException, match="The graph already has a different node"):
        g.add_node(Position3D(0, 1, 1), NodeType.X)


def test_zx_graph_add_edge() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.Z),
        ZXNode(Position3D(1, 0, 0), NodeType.X),
        has_hadamard=True,
    )
    assert g.num_nodes == 2
    assert g.num_edges == 1
    assert g.has_edge_between(Position3D(0, 0, 0), Position3D(1, 0, 0))
    assert g.get_edge(Position3D(0, 0, 0), Position3D(1, 0, 0)).has_hadamard

    with pytest.raises(TQECException, match="An edge must connect two nearby nodes."):
        g.add_edge(
            ZXNode(Position3D(0, 2, 0), NodeType.Z),
            ZXNode(Position3D(0, 0, 0), NodeType.X),
        )


def test_zx_graph_edges_at() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.Z),
        ZXNode(Position3D(1, 0, 0), NodeType.P),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.Z),
        ZXNode(Position3D(0, 1, 0), NodeType.P),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.Z),
        ZXNode(Position3D(-1, 0, 0), NodeType.P),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.Z),
        ZXNode(Position3D(0, -1, 0), NodeType.P),
    )
    assert len(g.edges_at(Position3D(0, 0, 0))) == 4
    assert len(g.edges_at(Position3D(1, 0, 0))) == 1


def test_zx_graph_fill_ports() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.P),
        ZXNode(Position3D(1, 0, 0), NodeType.X),
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 0), NodeType.X),
        ZXNode(Position3D(2, 0, 0), NodeType.P),
    )
    assert g.num_ports == 2
    with pytest.raises(TQECException, match="There is no port at"):
        g.fill_ports({Position3D(1, 0, 0): NodeType.Z})

    with pytest.raises(TQECException, match="Cannot fill the port"):
        g.fill_ports({Position3D(0, 0, 0): NodeType.P})

    g.fill_ports(NodeType.X)
    assert g.num_ports == 0
    assert g[Position3D(0, 0, 0)].node_type == NodeType.X
    assert g[Position3D(2, 0, 0)].node_type == NodeType.X


def test_zx_graph_with_zx_flipped() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.P),
        ZXNode(Position3D(1, 0, 0), NodeType.X),
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 0), NodeType.X),
        ZXNode(Position3D(2, 0, 0), NodeType.Z),
    )
    g.add_edge(
        ZXNode(Position3D(2, 0, 0), NodeType.Z),
        ZXNode(Position3D(2, 1, 0), NodeType.Y),
    )
    g.add_edge(
        ZXNode(Position3D(2, 0, 0), NodeType.Z),
        ZXNode(Position3D(2, 0, 1), NodeType.P),
    )
    assert g.num_nodes == 5

    flipped_g = g.with_zx_flipped()
    assert flipped_g.num_nodes == 5
    assert flipped_g[Position3D(0, 0, 0)].node_type == NodeType.P
    assert flipped_g[Position3D(1, 0, 0)].node_type == NodeType.Z
    assert flipped_g[Position3D(2, 0, 0)].node_type == NodeType.X
    assert flipped_g[Position3D(2, 1, 0)].node_type == NodeType.Y
    assert flipped_g[Position3D(2, 0, 1)].node_type == NodeType.P


def test_logical_cnot_zx_graph() -> None:
    g = logical_cnot_zx_graph("open")
    assert g.num_ports == 4
    assert g.num_nodes == 10
    assert len([n for n in g.nodes if n.node_type == NodeType.X]) == 2
    assert len([n for n in g.nodes if n.node_type == NodeType.Z]) == 4
    assert len(g.leaf_nodes) == 4
