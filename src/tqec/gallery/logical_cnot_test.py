from typing import Literal, cast
from tqec.computation.zx_graph import ZXKind
from tqec.gallery.logical_cnot import logical_cnot_zx_graph


def test_logical_cnot_zx_graph_open() -> None:
    g = logical_cnot_zx_graph("open")
    assert g.num_ports == 4
    assert g.num_nodes == 10
    assert g.num_edges == 9
    assert len(g.leaf_nodes) == 4
    assert len([n for n in g.nodes if n.kind == ZXKind.Z]) == 2
    assert len([n for n in g.nodes if n.kind == ZXKind.X]) == 4
    assert {*g.ports.keys()} == {
        "In_Control",
        "Out_Control",
        "In_Target",
        "Out_Target",
    }


def test_logical_cnot_zx_graph_filled() -> None:
    for port_type in ("x", "z"):
        g = logical_cnot_zx_graph(cast(Literal["x", "z"], port_type))
        assert g.num_ports == 0
        assert g.num_nodes == 10
        assert g.num_edges == 9
        assert len(g.leaf_nodes) == 4
        num_x_nodes = len([n for n in g.nodes if n.kind == ZXKind.X])
        num_z_nodes = len([n for n in g.nodes if n.kind == ZXKind.Z])
        if port_type == "x":
            assert num_x_nodes == 8
            assert num_z_nodes == 2
        else:
            assert num_x_nodes == 4
            assert num_z_nodes == 6


def test_logical_cnot_correlation_surface() -> None:
    g = logical_cnot_zx_graph("open")
    correlation_surfaces = g.find_correration_surfaces()
    all_external_stabilizers = [cs.external_stabilizer for cs in correlation_surfaces]
    assert all(
        [
            s in all_external_stabilizers
            for s in [
                {
                    "In_Control": "X",
                    "Out_Control": "X",
                    "In_Target": "I",
                    "Out_Target": "X",
                },
                {
                    "In_Control": "I",
                    "Out_Control": "I",
                    "In_Target": "X",
                    "Out_Target": "X",
                },
                {
                    "In_Control": "Z",
                    "Out_Control": "Z",
                    "In_Target": "I",
                    "Out_Target": "I",
                },
                {
                    "In_Control": "I",
                    "Out_Control": "Z",
                    "In_Target": "Z",
                    "Out_Target": "Z",
                },
                {
                    "In_Control": "X",
                    "Out_Control": "X",
                    "In_Target": "X",
                    "Out_Target": "I",
                },
                {
                    "In_Control": "Z",
                    "Out_Control": "I",
                    "In_Target": "Z",
                    "Out_Target": "Z",
                },
            ]
        ]
    )
