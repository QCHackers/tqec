from tqec.computation.zx_graph import NodeType
from tqec.gallery.logical_cnot import logical_cnot_zx_graph


def test_logical_cnot_zx_graph_open() -> None:
    g = logical_cnot_zx_graph("open")
    assert g.num_ports == 4
    assert g.num_nodes == 6
    assert g.num_edges == 9
    assert len(g.leaf_nodes) == 4
    assert len([n for n in g.nodes if n.node_type == NodeType.X]) == 2
    assert len([n for n in g.nodes if n.node_type == NodeType.Z]) == 4

def test_logical_cnot_zx_graph_filled() -> None:
    for port_type in ("x", "z"):
        g = logical_cnot_zx_graph(port_type)
        assert g.num_ports == 0
        assert g.num_nodes == 10
        assert g.num_edges == 9
        assert len(g.leaf_nodes) == 4
        num_x_nodes = len([n for n in g.nodes if n.node_type == NodeType.X])
        num_z_nodes = len([n for n in g.nodes if n.node_type == NodeType.Z])
        if port_type == "x":
            assert num_x_nodes == 6
            assert num_z_nodes == 4
        else:
            assert num_x_nodes == 2
            assert num_z_nodes == 8
