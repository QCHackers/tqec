from typing import Literal
from tqec.computation.block_graph.graph import BlockGraph
from tqec.computation.zx_graph import ZXGraph, ZXKind, ZXNode
from tqec.position import Position3D


def three_cnots_zx_graph(port_type: Literal["x", "z", "open"]) -> ZXGraph:
    """Three CNOT ZX graph.

    Implement the following circuit:
    ```
    CNOT 0 1
    CNOT 1 2
    CNOT 0 2
    ```
    """
    g = ZXGraph("Three CNOT")
    g.add_edge(
        ZXNode(Position3D(-1, 0, 0), ZXKind.P, "Out_a"),
        ZXNode(Position3D(0, 0, 0), ZXKind.Z),
    )
    g.add_edge(
        ZXNode(Position3D(0, -1, 0), ZXKind.P, "In_a"),
        ZXNode(Position3D(0, 0, 0), ZXKind.Z),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXKind.Z),
        ZXNode(Position3D(0, 1, 0), ZXKind.Z),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXKind.Z),
        ZXNode(Position3D(1, 0, 0), ZXKind.X),
    )
    g.add_edge(
        ZXNode(Position3D(0, 1, 0), ZXKind.Z),
        ZXNode(Position3D(1, 1, 0), ZXKind.X),
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, -1), ZXKind.P, "In_b"),
        ZXNode(Position3D(1, 0, 0), ZXKind.X),
    )
    g.add_edge(
        ZXNode(Position3D(1, 1, -1), ZXKind.P, "In_c"),
        ZXNode(Position3D(1, 1, 0), ZXKind.X),
    )
    g.add_edge(
        ZXNode(Position3D(1, 1, 0), ZXKind.X),
        ZXNode(Position3D(2, 1, 0), ZXKind.P, "Out_c"),
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 0), ZXKind.X),
        ZXNode(Position3D(1, 0, 1), ZXKind.Z),
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 1), ZXKind.Z),
        ZXNode(Position3D(1, 0, 2), ZXKind.P, "Out_b"),
    )
    g.add_edge(
        ZXNode(Position3D(1, 0, 1), ZXKind.Z),
        ZXNode(Position3D(1, 1, 1), ZXKind.Z),
    )
    g.add_edge(
        ZXNode(Position3D(1, 1, 0), ZXKind.X),
        ZXNode(Position3D(1, 1, 1), ZXKind.Z),
    )

    if port_type != "open":
        g.fill_ports(ZXKind(port_type.upper()))
    return g


def three_cnots_block_graph(port_type: Literal["x", "z", "open"]) -> BlockGraph:
    zx_graph = three_cnots_zx_graph(port_type)
    return zx_graph.to_block_graph("Three CNOT")
