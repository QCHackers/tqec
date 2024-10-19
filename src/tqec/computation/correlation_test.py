import pytest

from tqec.computation.correlation import CorrelationSurface
from tqec.computation.zx_graph import NodeType, ZXEdge, ZXGraph, ZXNode
from tqec.exceptions import TQECException
from tqec.position import Position3D


def test_correlation_single_xz_node() -> None:
    for node_type in [NodeType.X, NodeType.Z]:
        g = ZXGraph()
        g.add_node(Position3D(0, 0, 0), node_type)
        assert g.find_correration_surfaces() == {
            CorrelationSurface(
                ZXNode(Position3D(0, 0, 0), node_type.with_zx_flipped()), ""
            )
        }

    g = ZXGraph()
    g.add_x_node(Position3D(0, 0, 0))
    g.add_z_node(Position3D(1, 0, 0))
    with pytest.raises(
        TQECException,
        match="The graph must be a single connected component to find the correlation surfaces.",
    ):
        g.find_correration_surfaces()


def test_correlation_two_xz_node() -> None:
    for node_type in [NodeType.X, NodeType.Z]:
        g = ZXGraph()
        g.add_edge(
            ZXNode(Position3D(0, 0, 0), node_type),
            ZXNode(Position3D(0, 0, 1), node_type),
        )
        assert g.find_correration_surfaces() == {
            CorrelationSurface(
                frozenset(
                    [
                        ZXEdge(
                            ZXNode(Position3D(0, 0, 0), node_type.with_zx_flipped()),
                            ZXNode(Position3D(0, 0, 1), node_type.with_zx_flipped()),
                        )
                    ]
                ),
                "",
            )
        }

    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.X),
        ZXNode(Position3D(0, 0, 1), NodeType.Z),
    )
    assert g.find_correration_surfaces() == set()


def test_correlation_hadamard() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.X),
        ZXNode(Position3D(0, 0, 1), NodeType.Z),
        has_hadamard=True,
    )
    assert g.find_correration_surfaces() == {
        CorrelationSurface(
            frozenset(
                [
                    ZXEdge(
                        ZXNode(Position3D(0, 0, 0), NodeType.Z),
                        ZXNode(Position3D(0, 0, 1), NodeType.X),
                        has_hadamard=True,
                    )
                ]
            ),
            "",
        )
    }


def test_correlation_y_node() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.Y),
        ZXNode(Position3D(0, 0, 1), NodeType.P),
        port_label="out",
    )
    assert g.find_correration_surfaces() == {
        CorrelationSurface(
            frozenset(
                [
                    ZXEdge(
                        ZXNode(Position3D(0, 0, 0), NodeType.X),
                        ZXNode(Position3D(0, 0, 1), NodeType.X),
                    ),
                    ZXEdge(
                        ZXNode(Position3D(0, 0, 0), NodeType.Z),
                        ZXNode(Position3D(0, 0, 1), NodeType.Z),
                    ),
                ]
            ),
            "Y",
        )
    }


def test_correlation_port_passthrough():
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.P),
        ZXNode(Position3D(1, 0, 0), NodeType.Z),
        port_label="in",
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 0), NodeType.Z),
        ZXNode(Position3D(2, 0, 0), NodeType.P),
        port_label="out",
    )

    def _span(node_type: NodeType) -> frozenset[ZXEdge]:
        return frozenset(
            [
                ZXEdge(
                    ZXNode(Position3D(0, 0, 0), node_type),
                    ZXNode(Position3D(1, 0, 0), node_type),
                ),
                ZXEdge(
                    ZXNode(Position3D(1, 0, 0), node_type),
                    ZXNode(Position3D(2, 0, 0), node_type),
                ),
            ]
        )

    x_span = _span(NodeType.X)
    z_span = _span(NodeType.Z)

    assert g.find_correration_surfaces().issuperset(
        {
            CorrelationSurface(x_span, "XX"),
            CorrelationSurface(z_span, "ZZ"),
            CorrelationSurface(x_span | z_span, "YY"),
        }
    )


def test_correlation_logical_s_via_gate_teleportation() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.P),
        ZXNode(Position3D(0, 0, 1), NodeType.Z),
        port_label="in",
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 1), NodeType.Z),
        ZXNode(Position3D(0, 0, 2), NodeType.P),
        port_label="out",
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 1), NodeType.Z),
        ZXNode(Position3D(1, 0, 1), NodeType.Z),
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 1), NodeType.Z),
        ZXNode(Position3D(1, 0, 2), NodeType.Y),
    )
    correlation_surfaces = g.find_correration_surfaces()
    impl_external_stabilizers = {cs.external_stabilizer for cs in correlation_surfaces}
    assert all(
        [
            external_stabilizer in impl_external_stabilizers
            for external_stabilizer in ["ZZ", "XY", "YX"]
        ]
    )
