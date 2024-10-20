from typing import Literal
from tqec.computation.block_graph.graph import BlockGraph
from tqec.computation.zx_graph import ZXType, ZXGraph, ZXNode
from tqec.position import Position3D


def logical_cnot_zx_graph(port_type: Literal["z", "x", "open"]) -> ZXGraph:
    """Create the `ZXGraph` for the logical CNOT gate with the given port type."""
    if port_type != "open":
        name = f"Logical CNOT with {port_type}-basis ports"
    else:
        name = "Logical CNOT with open ports"
    g = ZXGraph(name)
    g.add_edge(
        ZXNode(Position3D(0, 0, 0), ZXType.P),
        ZXNode(Position3D(0, 0, 1), ZXType.Z),
        port_label="In_Control",
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 1), ZXType.Z),
        ZXNode(Position3D(0, 0, 2), ZXType.X),
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 2), ZXType.X),
        ZXNode(Position3D(0, 0, 3), ZXType.P),
        port_label="Out_Control",
    )
    g.add_edge(
        ZXNode(Position3D(0, 0, 1), ZXType.Z),
        ZXNode(Position3D(0, 1, 1), ZXType.Z),
    )
    g.add_edge(
        ZXNode(Position3D(0, 1, 1), ZXType.Z),
        ZXNode(Position3D(0, 1, 2), ZXType.X),
    )
    g.add_edge(
        ZXNode(Position3D(0, 1, 2), ZXType.X),
        ZXNode(Position3D(1, 1, 2), ZXType.X),
    )
    g.add_edge(
        ZXNode(Position3D(1, 1, 0), ZXType.P),
        ZXNode(Position3D(1, 1, 1), ZXType.X),
        port_label="In_Target",
    )
    g.add_edge(
        ZXNode(Position3D(1, 1, 1), ZXType.X),
        ZXNode(Position3D(1, 1, 2), ZXType.X),
    )
    g.add_edge(
        ZXNode(Position3D(1, 1, 2), ZXType.X),
        ZXNode(Position3D(1, 1, 3), ZXType.P),
        port_label="Out_Target",
    )

    if port_type != "open":
        g.fill_ports(ZXType(port_type.upper()))
    return g


def logical_cnot_block_graph(port_type: Literal["z", "x", "open"]) -> BlockGraph:
    """Create the `BlockGraph` for the logical CNOT gate with the given port type."""
    zx_graph = logical_cnot_zx_graph(port_type)
    return zx_graph.to_block_graph(zx_graph.name)
