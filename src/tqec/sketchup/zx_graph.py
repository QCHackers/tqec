"""ZX graph representation of a 3D spacetime defect diagram."""
from __future__ import annotations

from enum import Enum, auto
from dataclasses import dataclass, astuple

import networkx as nx

from tqec.exceptions import TQECException


class NodeType(Enum):
    """Valid node types in a ZX graph."""
    X = auto() # X-type node
    Z = auto() # Z-type node
    V = auto() # Virtual node that represents an open port


@dataclass(frozen=True, order=True)
class Position3D:
    """A 3D integer position."""
    x: int
    y: int
    z: int

    def shift_by(self, dx: int = 0, dy: int = 0, dz: int = 0) -> Position3D:
        """Shift the position by the given offset."""
        return Position3D(self.x + dx, self.y + dy, self.z + dz)

    def is_nearby(self, other: Position3D) -> bool:
        """Check if the other position is near to this position, i.e. Manhattan distance is 1."""
        return abs(self.x - other.x) + abs(self.y - other.y) + abs(self.z - other.z) == 1

    def __post_init__(self):
        if any(not isinstance(i, int) for i in astuple(self)):
            raise TQECException("Position must be an integer.")

    def __str__(self) -> str:
        return f"({self.x},{self.y},{self.z})"


@dataclass(frozen=True)
class ZXNode:
    position: Position3D
    node_type: NodeType


@dataclass(frozen=True)
class ZXEdge:
    u: ZXNode
    v: ZXNode
    has_hadamard: bool = False


_NODE_DATA_KEY = "node_data"
_EDGE_DATA_KEY = "edge_data"


class ZXGraph:
    def __init__(self, name: str) -> None:
        """An undirected graph representation of a 3D spacetime defect diagram.

        Despite the name, the graph is not exactly the ZX-calculus graph as rewrite rules
        can not be applied to the graph arbitrarily. The graph must correspond to a valid
        3D spacetime diagram, which can be realized with the lattice surgery on the 2D
        patches of surface code. And rewrite rules can only be applied with respect to a
        valid physical realization of the spacetime diagram.

        Note that not all ZX graph admits a valid spacetime diagram representation. And the
        graph construction **does not check** the validity constraints.
        """
        self._name = name
        # Internal undirected graph representation
        self._graph = nx.Graph()

    @property
    def name(self) -> str:
        """The name of the graph."""
        return self._name

    @property
    def num_nodes(self) -> int:
        """The number of nodes in the graph."""
        return self._graph.number_of_nodes()

    @property
    def num_edges(self) -> int:
        """The number of edges in the graph."""
        return self._graph.number_of_edges()

    @property
    def nodes(self) -> list[ZXNode]:
        """Return a list of nodes in the graph."""
        return [data[_NODE_DATA_KEY] for _, data in self._graph.nodes(data=True)]


    @property
    def edges(self) -> list[ZXEdge]:
        """Return a list of edges in the graph."""
        return [data[_EDGE_DATA_KEY] for _, _, data in self._graph.edges(data=True)]

    def add_node(
        self,
        position: Position3D,
        node_type: NodeType,
    ) -> None:
        """Add a node to the graph.

        Args:
            position: The 3D position of the node.
            node_type: The type of the node.
        """
        if position in self._graph:
            raise TQECException(f"Node {position} already exists in the graph.")
        self._graph.add_node(position, _NODE_DATA_KEY=ZXNode(position, node_type))

    def add_edge(self, u: Position3D, v: Position3D, has_hadamard: bool = False) -> None:
        """Add an edge to the graph.

        Args:
            u: The position of the first node.
            v: The position of the second node.
            has_hadamard: Whether the edge has a Hadamard transition.
        """
        if u not in self._graph or v not in self._graph:
            raise TQECException("Both nodes must exist in the graph.")
        if not u.is_nearby(v):
            raise TQECException("The two nodes must be nearby in the 3D space to be connected.")
        u_node = self._graph.nodes[u][_NODE_DATA_KEY]
        v_node = self._graph.nodes[v][_NODE_DATA_KEY]
        self._graph.add_edge(u, v, _EDGE_DATA_KEY=(u_node, v_node, has_hadamard))

    def get_node(self, position: Position3D) -> ZXNode | None:
        """Get the node by position."""
        if position not in self._graph:
            return None
        return self._graph.nodes[position][_NODE_DATA_KEY]

    def get_edge(self, u: Position3D, v: Position3D) -> ZXEdge | None:
        """Get the edge by its endpoint positions."""
        if not self._graph.has_edge(u, v):
            return None
        return self._graph.edges[u, v][_EDGE_DATA_KEY]
