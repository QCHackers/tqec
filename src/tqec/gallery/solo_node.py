from typing import Literal

from tqec.computation.block_graph import BlockGraph
from tqec.computation.zx_graph import ZXGraph, ZXKind, ZXNode
from tqec.position import Position3D


def solo_node_zx_graph(basis: Literal["Z", "X"]) -> ZXGraph:
    """Get a ZX graph with a single node of the given basis."""
    g = ZXGraph(f"Solo {basis} Node")
    g.add_node(ZXNode(Position3D(0, 0, 0), ZXKind(basis)))
    return g


def solo_node_block_graph(basis: Literal["Z", "X"]) -> BlockGraph:
    """Get a block graph with a single node of the given basis."""
    zx_graph = solo_node_zx_graph(basis)
    return zx_graph.to_block_graph(zx_graph.name)
