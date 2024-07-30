import pytest

from tqec.sketchup.zx_graph import (
    Position3D,
    Direction3D,
    NodeType,
    ZXNode,
    ZXEdge,
    ZXGraph,
)

from tqec.exceptions import TQECException


def test_position_3d() -> None:
    p1 = Position3D(0, 0, 0)
    assert p1.as_tuple() == (0, 0, 0)
    assert p1.shift_by(1, 2, 3) == Position3D(1, 2, 3)
    assert p1.is_nearby(Position3D(0, 0, 1))
    assert p1.is_nearby(Position3D(0, 1, 0))
    assert p1.is_nearby(Position3D(-1, 0, 0))
    assert not p1.is_nearby(Position3D(1, 0, 1))
    assert not p1.is_nearby(Position3D(0, -1, 1))
    with pytest.raises(TQECException, match="Position must be an integer"):
        Position3D(0.5, 0, 0)


def test_direction_3d() -> None:
    assert Direction3D.X.axis_index == 0
    assert Direction3D.Y.axis_index == 1
    assert Direction3D.Z.axis_index == 2
    assert Direction3D.from_axis_index(0) == Direction3D.X
    assert Direction3D.from_axis_index(1) == Direction3D.Y
    assert Direction3D.from_axis_index(2) == Direction3D.Z
    assert Direction3D.all() == [Direction3D.X, Direction3D.Y, Direction3D.Z]


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
