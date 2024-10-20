import pytest

from tqec.exceptions import TQECException
from tqec.position import Direction3D, Position3D
from tqec.computation.zx_graph import ZXType, ZXEdge, ZXGraph, ZXNode


def test_zx_node() -> None:
    node = ZXNode(Position3D(0, 0, 0), ZXType.Z)
    assert not node.is_port
    assert str(node) == "Z(0,0,0)"

    node = ZXNode(Position3D(0, 1, 4), ZXType.P)
    assert node.is_port
    assert str(node) == "PORT(0,1,4)"



def test_zx_edge() -> None:
    edge = ZXEdge(
        ZXNode(Position3D(2, 0, 0), ZXType.Z),
        ZXNode(Position3D(1, 0, 0), ZXType.X),
    )
    assert edge.u.position == Position3D(1, 0, 0)
    assert edge.v.position == Position3D(2, 0, 0)
    assert edge.direction == Direction3D.X
    assert str(edge) == "X(1,0,0)-Z(2,0,0)"

    with pytest.raises(TQECException, match="An edge must connect two nearby nodes."):
        ZXEdge(
            ZXNode(Position3D(0, 0, 0), ZXType.Z),
            ZXNode(Position3D(2, 0, 0), ZXType.Z),
        )

    with pytest.raises(TQECException, match="Cannot create an edge between two ports."):
        ZXEdge(
            ZXNode(Position3D(0, 0, 0), ZXType.P),
            ZXNode(Position3D(1, 0, 0), ZXType.P),
        )
    with pytest.raises(
        TQECException, match="An edge with Y-type node must be in the Z-direction."
    ):
        ZXEdge(
            ZXNode(Position3D(0, 0, 0), ZXType.Y),
            ZXNode(Position3D(1, 0, 0), ZXType.Z),
        )


def test_zx_graph_construction() -> None:
    g = ZXGraph("Test ZX Graph")
    assert g.name == "Test ZX Graph"
    assert len(g.nodes) == 0
    assert len(g.edges) == 0


def test_zx_graph_add_node() -> None:
    g = ZXGraph()
    g.add_node(Position3D(0, 0, 0), ZXType.Z)
    assert g.num_nodes == 1
    assert g[Position3D(0, 0, 0)].node_type == ZXType.Z
    assert Position3D(0, 0, 0) in g

    g.add_x_node(Position3D(0, 1, 1))
    assert g.num_nodes == 2

    with pytest.raises(TQECException, match="Cannot add a P or Y-type node solely"):
        g.add_node(Position3D(2, 0, 0), ZXType.P)

    with pytest.raises(TQECException, match="Cannot add a P or Y-type node solely"):
        g.add_node(Position3D(2, 0, 0), ZXType.Y)

    with pytest.raises(TQECException, match="The graph already has a different node"):
        g.add_node(Position3D(0, 1, 1), ZXType.Z)


def test_zx_graph_add_edge() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXType.Z),
        ZXNode(Position3D(1, 0, 0), ZXType.X),
        has_hadamard=True,
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 1), ZXType.Y),
        ZXNode(Position3D(1, 0, 0), ZXType.X),
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 0), ZXType.X),
        ZXNode(Position3D(2, 0, 0), ZXType.P),
        port_label="out",
    )
    assert g.num_nodes == 3
    assert g.num_edges == 3
    assert g.num_ports == 1
    assert g.ports == {"out": Position3D(2, 0, 0)}
    assert g.has_edge_between(Position3D(0, 0, 0), Position3D(1, 0, 0))
    assert g.get_edge(Position3D(0, 0, 0), Position3D(1, 0, 0)).has_hadamard

    with pytest.raises(TQECException, match="An edge must connect two nearby nodes."):
        g.add_edge(
            ZXNode(Position3D(0, 2, 0), ZXType.Z),
            ZXNode(Position3D(0, 0, 0), ZXType.X),
        )

    with pytest.raises(TQECException, match="Cannot create an edge between two ports."):
        g.add_edge(
            ZXNode(Position3D(2, 0, 0), ZXType.P),
            ZXNode(Position3D(3, 0, 0), ZXType.P),
        )

    with pytest.raises(
        TQECException, match="The edge includes a port, a port label must be provided."
    ):
        g.add_edge(
            ZXNode(Position3D(-1, 0, 0), ZXType.P),
            ZXNode(Position3D(0, 0, 0), ZXType.Z),
        )

    with pytest.raises(TQECException, match="should have at most one edge."):
        g.add_edge(
            ZXNode(Position3D(2, 0, 0), ZXType.P),
            ZXNode(Position3D(3, 0, 0), ZXType.Z),
            port_label="p",
        )
    with pytest.raises(TQECException, match="should have at most one edge."):
        g.add_edge(
            ZXNode(Position3D(1, 0, 1), ZXType.Y),
            ZXNode(Position3D(1, 0, 2), ZXType.Z),
        )
    with pytest.raises(
        TQECException, match="There is already a port with label out in the graph"
    ):
        g.add_edge(
            ZXNode(Position3D(-1, 0, 0), ZXType.P),
            ZXNode(Position3D(0, 0, 0), ZXType.Z),
            port_label="out",
        )


def test_zx_graph_edges_at() -> None:
    g = ZXGraph()
    for i, pos in enumerate(
        [
            Position3D(1, 0, 0),
            Position3D(0, 1, 0),
            Position3D(-1, 0, 0),
            Position3D(0, -1, 0),
        ]
    ):
        g.add_edge(
            ZXNode(Position3D(0, 0, 0), ZXType.Z),
            ZXNode(pos, ZXType.P),
            port_label=f"p{i}",
        )
    assert len(g.edges_at(Position3D(0, 0, 0))) == 4
    assert len(g.edges_at(Position3D(1, 0, 0))) == 1


def test_zx_graph_fill_ports() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXType.P),
        ZXNode(Position3D(1, 0, 0), ZXType.X),
        port_label="in",
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 0), ZXType.X),
        ZXNode(Position3D(2, 0, 0), ZXType.P),
        port_label="out",
    )
    assert g.num_nodes == 1
    assert g.num_ports == 2
    with pytest.raises(TQECException, match="There is no port with label unknown"):
        g.fill_ports({"unknown": ZXType.Z})

    with pytest.raises(TQECException, match="Cannot fill the ports with port type"):
        g.fill_ports({"in": ZXType.P})

    g.fill_ports(ZXType.X)
    assert g.num_ports == 0
    assert g[Position3D(0, 0, 0)].node_type == ZXType.X
    assert g[Position3D(2, 0, 0)].node_type == ZXType.X
    new_edge = g.get_edge(Position3D(0, 0, 0), Position3D(1, 0, 0))
    assert new_edge.u == ZXNode(Position3D(0, 0, 0), ZXType.X)
    assert new_edge.v == ZXNode(Position3D(1, 0, 0), ZXType.X)
    assert g.num_nodes == 3
    assert g.num_ports == 0


def test_zx_graph_with_zx_flipped() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXType.P),
        ZXNode(Position3D(1, 0, 0), ZXType.X),
        port_label="p1",
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 0), ZXType.X),
        ZXNode(Position3D(2, 0, 0), ZXType.Z),
    )
    g.add_edge(
        ZXNode(Position3D(2, 0, 0), ZXType.Z),
        ZXNode(Position3D(2, 0, -1), ZXType.Y),
    )
    g.add_edge(
        ZXNode(Position3D(2, 0, 0), ZXType.Z),
        ZXNode(Position3D(2, 0, 1), ZXType.P),
        port_label="p2",
    )
    assert g.num_nodes == 3
    assert g.num_ports == 2
    assert g.num_edges == 4

    flipped_g = g.with_zx_flipped()
    assert flipped_g.num_nodes == 3
    assert g.num_ports == 2
    assert g.num_edges == 4
    assert flipped_g[Position3D(0, 0, 0)].node_type == ZXType.P
    assert flipped_g[Position3D(1, 0, 0)].node_type == ZXType.Z
    assert flipped_g[Position3D(2, 0, 0)].node_type == ZXType.X
    assert flipped_g[Position3D(2, 0, -1)].node_type == ZXType.Y
    assert flipped_g[Position3D(2, 0, 1)].node_type == ZXType.P
