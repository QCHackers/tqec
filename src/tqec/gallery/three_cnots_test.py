from tqec.computation.zx_graph import NodeType
from tqec.gallery.three_cnots import three_cnots_zx_graph


def test_three_cnots_zx_graph_open() -> None:
    g = three_cnots_zx_graph("open")
    assert g.num_ports == 6
    assert g.num_nodes == 6
    assert g.num_edges == 12
    assert len(g.leaf_nodes) == 6
    assert len([n for n in g.nodes if n.node_type == NodeType.Z]) == 4
    assert len([n for n in g.nodes if n.node_type == NodeType.X]) == 2
    assert g.ordered_port_labels == [
        "Out_a",
        "In_a",
        "In_b",
        "Out_b",
        "In_c",
        "Out_c",
    ]


def test_three_cnots_zx_graph_filled() -> None:
    for port_type in ("x", "z"):
        g = three_cnots_zx_graph(port_type)
        assert g.num_ports == 0
        assert g.num_nodes == 12
        assert g.num_edges == 12
        assert len(g.leaf_nodes) == 6
        num_x_nodes = len([n for n in g.nodes if n.node_type == NodeType.X])
        num_z_nodes = len([n for n in g.nodes if n.node_type == NodeType.Z])
        if port_type == "x":
            assert num_x_nodes == 8
            assert num_z_nodes == 4
        else:
            assert num_x_nodes == 2
            assert num_z_nodes == 10


def test_three_cnots_correlation_surface() -> None:
    g = three_cnots_zx_graph("open")
    correlation_surfaces = g.find_correration_surfaces()
    all_external_stabilizers = {cs.external_stabilizer for cs in correlation_surfaces}
    # Pauli string in order `a'abb'cc'`
    expected_stabilizers = [
        "XXX_X_",
        "ZZ____",
        "__XXX_",
        "_ZZZ__",
        "____XX",
        "__Z_ZZ"
    ]
    assert all([s in all_external_stabilizers for s in expected_stabilizers])
