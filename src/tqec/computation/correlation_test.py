import pytest

from tqec.computation.correlation import CorrelationSurface
from tqec.computation.zx_graph import ZXKind, ZXEdge, ZXGraph, ZXNode
from tqec.exceptions import TQECException
from tqec.position import Position3D


def test_correlation_single_xz_node() -> None:
    for kind in [ZXKind.X, ZXKind.Z]:
        g = ZXGraph()
        g.add_node(Position3D(0, 0, 0), kind)
        assert g.find_correration_surfaces() == [
            CorrelationSurface(ZXNode(Position3D(0, 0, 0), kind.with_zx_flipped()), {})
        ]

    g = ZXGraph()
    g.add_node(Position3D(0, 0, 0), ZXKind.X)
    g.add_node(Position3D(1, 0, 0), ZXKind.Z)
    with pytest.raises(TQECException):
        g.find_correration_surfaces()


def test_correlation_two_xz_node() -> None:
    for kind in [ZXKind.X, ZXKind.Z]:
        g = ZXGraph()
        g.add_edge(
            ZXNode(Position3D(0, 0, 0), kind),
            ZXNode(Position3D(0, 0, 1), kind),
        )
        assert g.find_correration_surfaces() == [
            CorrelationSurface(
                frozenset(
                    [
                        ZXEdge(
                            ZXNode(Position3D(0, 0, 0), kind.with_zx_flipped()),
                            ZXNode(Position3D(0, 0, 1), kind.with_zx_flipped()),
                        )
                    ]
                ),
                {},
            )
        ]

    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXKind.X),
        ZXNode(Position3D(0, 0, 1), ZXKind.Z),
    )
    assert g.find_correration_surfaces() == []


def test_correlation_hadamard() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXKind.X),
        ZXNode(Position3D(0, 0, 1), ZXKind.Z),
        has_hadamard=True,
    )
    assert g.find_correration_surfaces() == [
        CorrelationSurface(
            frozenset(
                [
                    ZXEdge(
                        ZXNode(Position3D(0, 0, 0), ZXKind.Z),
                        ZXNode(Position3D(0, 0, 1), ZXKind.X),
                        has_hadamard=True,
                    )
                ]
            ),
            {},
        )
    ]


def test_correlation_y_node() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXKind.Y),
        ZXNode(Position3D(0, 0, 1), ZXKind.P, "out"),
    )
    assert g.find_correration_surfaces() == [
        CorrelationSurface(
            frozenset(
                [
                    ZXEdge(
                        ZXNode(Position3D(0, 0, 0), ZXKind.X),
                        ZXNode(Position3D(0, 0, 1), ZXKind.X),
                    ),
                    ZXEdge(
                        ZXNode(Position3D(0, 0, 0), ZXKind.Z),
                        ZXNode(Position3D(0, 0, 1), ZXKind.Z),
                    ),
                ]
            ),
            {"out": "Y"},
        )
    ]


def test_correlation_port_passthrough():
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXKind.P, "in"),
        ZXNode(Position3D(1, 0, 0), ZXKind.Z),
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 0), ZXKind.Z),
        ZXNode(Position3D(2, 0, 0), ZXKind.P, "out"),
    )

    def _span(node_type: ZXKind) -> frozenset[ZXEdge]:
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

    x_span = _span(ZXKind.X)
    z_span = _span(ZXKind.Z)

    assert set(g.find_correration_surfaces()) == {
        CorrelationSurface(x_span, {"in": "X", "out": "X"}),
        CorrelationSurface(z_span, {"in": "Z", "out": "Z"}),
    }


def test_correlation_logical_s_via_gate_teleportation() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXKind.P, "in"),
        ZXNode(Position3D(0, 0, 1), ZXKind.Z),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 1), ZXKind.Z),
        ZXNode(Position3D(0, 0, 2), ZXKind.P, "out"),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 1), ZXKind.Z),
        ZXNode(Position3D(1, 0, 1), ZXKind.Z),
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 1), ZXKind.Z),
        ZXNode(Position3D(1, 0, 2), ZXKind.Y),
    )
    correlation_surfaces = g.find_correration_surfaces()
    impl_external_stabilizers = [cs.external_stabilizer for cs in correlation_surfaces]
    assert all(
        [
            s in impl_external_stabilizers
            for s in [
                {"in": "Z", "out": "Z"},
                {"in": "X", "out": "Y"},
                {"in": "Y", "out": "X"},
            ]
        ]
    )


def test_correlation_y_init_follow_measure() -> None:
    g = ZXGraph()
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXKind.Y),
        ZXNode(Position3D(0, 0, -1), ZXKind.X),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, -1), ZXKind.X),
        ZXNode(Position3D(0, 0, -2), ZXKind.P, "in"),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXKind.Y),
        ZXNode(Position3D(0, 0, 1), ZXKind.Z),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 1), ZXKind.Z),
        ZXNode(Position3D(0, 0, 2), ZXKind.P, "out"),
    )
    correlation_surfaces = g.find_correration_surfaces()
    assert len(correlation_surfaces) == 2
    assert correlation_surfaces[0].external_stabilizer == {"in": "I", "out": "Y"}
    assert correlation_surfaces[1].external_stabilizer == {"in": "Y", "out": "I"}
