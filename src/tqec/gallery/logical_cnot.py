from typing import Literal
from tqec.computation.block_graph.graph import BlockGraph
from tqec.computation.zx_graph import NodeType, ZXGraph, ZXNode
from tqec.position import Position3D


def logical_cnot_zx_graph(port_type: Literal["z", "x", "open"]) -> ZXGraph:
    """Create the `ZXGraph` for the logical CNOT gate with the given port type."""
    if port_type != "open":
        name = f"Logical CNOT with {port_type}-basis ports"
    else:
        name = "Logical CNOT with open ports"
    graph = ZXGraph(name)
    graph.add_edge(
        ZXNode(Position3D(0, 0, 0), NodeType.P, "In_Control"),
        ZXNode(Position3D(0, 0, 1), NodeType.X),
    )
    graph.add_edge(
        ZXNode(Position3D(0, 0, 1), NodeType.X),
        ZXNode(Position3D(0, 0, 2), NodeType.Z),
    )
    graph.add_edge(
        ZXNode(Position3D(0, 0, 2), NodeType.Z),
        ZXNode(Position3D(0, 0, 3), NodeType.P, "Out_Control"),
    )
    graph.add_edge(
        ZXNode(Position3D(0, 0, 1), NodeType.X),
        ZXNode(Position3D(0, 1, 1), NodeType.X),
    )
    graph.add_edge(
        ZXNode(Position3D(0, 1, 1), NodeType.X),
        ZXNode(Position3D(0, 1, 2), NodeType.Z),
    )
    graph.add_edge(
        ZXNode(Position3D(0, 1, 2), NodeType.Z),
        ZXNode(Position3D(1, 1, 2), NodeType.Z),
    )
    graph.add_edge(
        ZXNode(Position3D(1, 1, 0), NodeType.P, "In_Target"),
        ZXNode(Position3D(1, 1, 1), NodeType.Z),
    )
    graph.add_edge(
        ZXNode(Position3D(1, 1, 1), NodeType.Z),
        ZXNode(Position3D(1, 1, 2), NodeType.Z),
    )
    graph.add_edge(
        ZXNode(Position3D(1, 1, 2), NodeType.Z),
        ZXNode(Position3D(1, 1, 3), NodeType.P, "Out_Target"),
    )

    if port_type != "open":
        graph.fill_ports(NodeType(port_type.upper()))
    return graph


def logical_cnot_block_graph(port_type: Literal["z", "x", "open"]) -> BlockGraph:
    """Create the `BlockGraph` for the logical CNOT gate with the given port type."""
    zx_graph = logical_cnot_zx_graph(port_type)
    return zx_graph.to_block_graph(zx_graph.name)
