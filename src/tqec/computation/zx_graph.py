"""ZX graph representation of a 3D spacetime defect diagram."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, cast

import networkx as nx

from tqec.exceptions import TQECException
from tqec.position import Direction3D, Position3D

if TYPE_CHECKING:
    from tqec.computation.block_graph import BlockGraph


class NodeType(Enum):
    """Valid node types in a ZX graph."""

    X = "X"
    Y = "Y"
    Z = "Z"
    P = "PORT"  # Open port for the input/ouput of the computation

    def dual(self) -> NodeType:
        if self == NodeType.X:
            return NodeType.Z
        elif self == NodeType.Z:
            return NodeType.X
        else:
            return self


@dataclass(frozen=True)
class ZXNode:
    """A node in the ZX graph.

    Attributes:
        type: The type of the node.
        position: The 3D position of the node.
    """

    position: Position3D
    node_type: NodeType

    @property
    def is_port(self) -> bool:
        """Check if the node is an open port, i.e. represents the input/output
        of the computation."""
        return self.node_type == NodeType.P


@dataclass(frozen=True)
class ZXEdge:
    """An edge in the ZX graph.

    Attributes:
        u: The first node of the edge, which has smaller position than `v`.
        v: The second node of the edge, which has larger position than `u`.
        has_hadamard: Whether the edge has a Hadamard transition.
    """

    u: ZXNode
    v: ZXNode
    has_hadamard: bool = False

    def __post_init__(self) -> None:
        if not self.u.position.is_neighbour(self.v.position):
            raise TQECException("An edge must connect two nearby nodes.")
        # Ensure position of u is less than v
        u, v = self.u, self.v
        if self.u.position > self.v.position:
            object.__setattr__(self, "u", v)
            object.__setattr__(self, "v", u)

    @property
    def direction(self) -> Direction3D:
        """Get the 3D direction of the edge."""
        u, v = self.u.position, self.v.position
        if u.x != v.x:
            return Direction3D.X
        if u.y != v.y:
            return Direction3D.Y
        return Direction3D.Z


_NODE_DATA_KEY = "tqec_zx_node_data"
_EDGE_DATA_KEY = "tqec_zx_edge_data"


class ZXGraph:
    def __init__(self, name: str = "") -> None:
        """An undirected graph representation of the logical computation.

        Despite the name, the graph is not exactly the ZX-calculus graph
        as rewrite rules can not be applied to the graph arbitrarily.
        The graph must correspond to a valid 3D spacetime diagram, which
        can be realized with the lattice surgery on the 2D patches of
        surface code. And rewrite rules can only be applied with respect
        to a valid physical realization of the spacetime diagram.

        Note that not all ZX graph admits a valid spacetime diagram
        representation. And the graph construction **does not check**
        the validity constraints.
        """
        self._name = name
        # Internal undirected graph representation
        self._graph = nx.Graph()

    @property
    def name(self) -> str:
        """The name of the graph."""
        return self._name

    @property
    def nx_graph(self) -> nx.Graph:
        """The internal networkx graph representation."""
        return self._graph

    @property
    def num_nodes(self) -> int:
        """The number of nodes in the graph."""
        return cast(int, self._graph.number_of_nodes())

    @property
    def num_edges(self) -> int:
        """The number of edges in the graph."""
        return cast(int, self._graph.number_of_edges())

    @property
    def nodes(self) -> list[ZXNode]:
        """Return a list of `ZXNode`s in the graph."""
        return [data[_NODE_DATA_KEY] for _, data in self._graph.nodes(data=True)]

    @property
    def edges(self) -> list[ZXEdge]:
        """Return a list of edges in the graph."""
        return [data[_EDGE_DATA_KEY] for _, _, data in self._graph.edges(data=True)]

    @property
    def leaf_nodes(self) -> list[ZXNode]:
        """Get the leaf nodes of the graph."""
        return [node for node in self.nodes if self._node_degree(node) == 1]

    @property
    def isolated_nodes(self) -> list[ZXNode]:
        """Get the isolated nodes of the graph."""
        return [node for node in self.nodes if self._node_degree(node) == 0]

    def _node_degree(self, node: ZXNode) -> int:
        return self._graph.degree(node.position)  # type: ignore

    def add_node(
        self,
        position: Position3D,
        node_type: NodeType,
    ) -> None:
        """Add a node to the graph.

        If the a node already exists at the position, the node type will be updated.

        Args:
            position: The 3D position of the node.
            node_type: The type of the node.
        """
        self._graph.add_node(position, **{_NODE_DATA_KEY: ZXNode(position, node_type)})

    def add_x_node(self, position: Position3D) -> None:
        """Add an X-type node to the graph."""
        self.add_node(position, NodeType.X)

    def add_y_node(self, position: Position3D) -> None:
        """Add an Y-type node to the graph."""
        self.add_node(position, NodeType.Y)

    def add_z_node(self, position: Position3D) -> None:
        """Add a Z-type node to the graph."""
        self.add_node(position, NodeType.Z)

    def add_port(self, position: Position3D) -> None:
        """Add an open port to the graph."""
        self.add_node(position, NodeType.P)

    def add_edge(
        self,
        u: ZXNode,
        v: ZXNode,
        has_hadamard: bool = False,
    ) -> None:
        """Add an edge to the graph.

        If the nodes do not exist in the graph, the nodes will be created.

        Args:
            u: The first node of the edge.
            v: The second node of the edge.
            has_hadamard: Whether the edge has a Hadamard transition.

        Raises:
            TQECException: If the edge does not connect two nearby nodes.
        """
        if not u.position.is_neighbour(v.position):
            raise TQECException("An edge must connect two nearby nodes.")
        self._graph.add_node(u.position, **{_NODE_DATA_KEY: u})
        self._graph.add_node(v.position, **{_NODE_DATA_KEY: v})
        self._graph.add_edge(
            u.position, v.position, **{_EDGE_DATA_KEY: ZXEdge(u, v, has_hadamard)}
        )

    def __contains__(self, position: Position3D) -> bool:
        return position in self._graph

    def __getitem__(self, position: Position3D) -> ZXNode:
        return cast(ZXNode, self._graph.nodes[position][_NODE_DATA_KEY])

    def has_edge_between(self, pos1: Position3D, pos2: Position3D) -> bool:
        """Check if there is an edge between two positions."""
        return self._graph.has_edge(pos1, pos2)

    def get_edge(self, pos1: Position3D, pos2: Position3D) -> ZXEdge:
        """Get the edge by its endpoint positions.

        Args:
            pos1: The first endpoint position.
            pos2: The second endpoint position.

        Returns:
            The edge between the two positions.

        Raises:
            TQECException: If there is no edge between the given positions.
        """
        if not self.has_edge_between(pos1, pos2):
            raise TQECException("No edge between the given positions in the graph.")
        return cast(ZXEdge, self._graph.edges[pos1, pos2][_EDGE_DATA_KEY])

    def edges_at(self, position: Position3D) -> list[ZXEdge]:
        """Get the edges incident to a position.

        Raises:
            TQECException: If there is no node at the given position in the graph.
        """
        if position not in self:
            raise TQECException("No node at the given position in the graph.")
        return [
            data[_EDGE_DATA_KEY]
            for _, _, data in self._graph.edges(position, data=True)
        ]

    def to_block_graph(self, name: str = "") -> BlockGraph:
        """Construct a block graph from a ZX graph.

        The ZX graph includes the minimal information required to construct the block graph,
        but not guaranteed to admit a valid block structure. The block structure will be inferred
        from the ZX graph and validated.

        Args:
            name: The name of the new block graph.

        Returns:
            The constructed block graph.
        """
        from tqec.computation.block_graph import BlockGraph

        return BlockGraph.from_zx_graph(self, name=name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ZXGraph):
            return False
        return cast(bool, nx.utils.graphs_equal(self._graph, other._graph))
