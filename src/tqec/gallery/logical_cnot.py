from typing import Literal
from tqec.computation.block_graph import BlockGraph
from tqec.computation.zx_graph import ZXKind, ZXGraph, ZXNode
from tqec.position import Position3D


def logical_cnot_zx_graph(port_type: Literal["Z", "X", "OPEN"]) -> ZXGraph:
    """Create the `ZXGraph` for the logical CNOT gate with the given port
    type."""
    if port_type != "OPEN":
        name = f"Logical CNOT with {port_type}-basis ports"
    else:
        name = "Logical CNOT with open ports"
    g = ZXGraph(name)
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXKind.P, "In_Control"),
        ZXNode(Position3D(0, 0, 1), ZXKind.Z),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 1), ZXKind.Z),
        ZXNode(Position3D(0, 0, 2), ZXKind.X),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 2), ZXKind.X),
        ZXNode(Position3D(0, 0, 3), ZXKind.P, "Out_Control"),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 1), ZXKind.Z),
        ZXNode(Position3D(0, 1, 1), ZXKind.Z),
    )
    g.add_edge(
        ZXNode(Position3D(0, 1, 1), ZXKind.Z),
        ZXNode(Position3D(0, 1, 2), ZXKind.X),
    )
    g.add_edge(
        ZXNode(Position3D(0, 1, 2), ZXKind.X),
        ZXNode(Position3D(1, 1, 2), ZXKind.X),
    )
    g.add_edge(
        ZXNode(Position3D(1, 1, 0), ZXKind.P, "In_Target"),
        ZXNode(Position3D(1, 1, 1), ZXKind.X),
    )
    g.add_edge(
        ZXNode(Position3D(1, 1, 1), ZXKind.X),
        ZXNode(Position3D(1, 1, 2), ZXKind.X),
    )
    g.add_edge(
        ZXNode(Position3D(1, 1, 2), ZXKind.X),
        ZXNode(Position3D(1, 1, 3), ZXKind.P, "Out_Target"),
    )

    if port_type != "OPEN":
        g.fill_ports(ZXKind(port_type))
    return g


def logical_cnot_block_graph(port_type: Literal["Z", "X", "OPEN"]) -> BlockGraph:
    """Create the `BlockGraph` for the logical CNOT gate with the given port
    type."""
    zx_graph = logical_cnot_zx_graph(port_type)
    return zx_graph.to_block_graph(zx_graph.name)
