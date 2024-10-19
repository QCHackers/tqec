"""ZX graph representation of a 3D spacetime defect diagram."""

from __future__ import annotations

from collections.abc import Mapping
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

    def with_zx_flipped(self) -> NodeType:
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
        position: The 3D position of the node.
        node_type: The type of the node.
    """

    position: Position3D
    node_type: NodeType

    @property
    def is_port(self) -> bool:
        """Check if the node is an open port, i.e. represents the input/output
        of the computation."""
        return self.node_type == NodeType.P

    @property
    def with_zx_flipped(self) -> ZXNode:
        """Get a new node with the node type flipped."""
        return ZXNode(self.position, self.node_type.with_zx_flipped())


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
        if self.u.is_port and self.v.is_port:
            raise TQECException("Cannot create an edge between two ports.")
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
        self._ports: dict[str, Position3D] = {}

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
        """The number of nodes in the graph, excluding the ports."""
        return cast(int, self._graph.number_of_nodes()) - self.num_ports

    @property
    def num_ports(self) -> int:
        """The number of open ports in the graph."""
        return len([node for node in self.nodes if node.is_port])

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
        """Get the leaf nodes of the graph, including the ports."""
        return [node for node in self.nodes if self._node_degree(node) == 1]

    @property
    def ports(self) -> dict[str, Position3D]:
        """Get the position of open ports of the graph."""
        return self._ports

    def is_port(self, position: Position3D) -> bool:
        """Check if the node at the position is an open port."""
        return position in self._ports.values()

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
        if node_type == NodeType.P:
            raise TQECException(
                "A port cannot be added solely, please use `add_edge` instead."
            )
        node = ZXNode(position, node_type)
        self._check_node_conflict(node)
        self._graph.add_node(position, **{_NODE_DATA_KEY: node})

    def _check_node_conflict(self, new_node: ZXNode) -> None:
        """Check whether a new node can be added to the graph without conflict."""
        position = new_node.position
        if position in self and self[position] != new_node:
            raise TQECException(
                f"The graph already has a different node {self[position]} at this position."
            )

    def add_x_node(self, position: Position3D) -> None:
        """Add an X-type node to the graph."""
        self.add_node(position, NodeType.X)

    def add_y_node(self, position: Position3D) -> None:
        """Add an Y-type node to the graph."""
        self.add_node(position, NodeType.Y)

    def add_z_node(self, position: Position3D) -> None:
        """Add a Z-type node to the graph."""
        self.add_node(position, NodeType.Z)

    def add_edge(
        self,
        u: ZXNode,
        v: ZXNode,
        has_hadamard: bool = False,
        port_label: str | None = None,
    ) -> None:
        """Add an edge to the graph. If the nodes do not exist in the graph,
        the nodes will be created.

        A port can only be added to the graph using this method along with an edge.

        Args:
            u: The first node of the edge.
            v: The second node of the edge.
            has_hadamard: Whether the edge has a Hadamard transition.
            port_label: The label of the port, if one of the nodes is a port. Required
                if the edge includes a port.

        Raises:
            TQECException: If the edge does not connect two nearby nodes.
            TQECException: If add the edge to two ports.
            TQECException: If add the edge to a port that already has an edge.
            TQECException: If the edge includes a port, but the port label is not provided.
            TQECException: If the edge includes a port, but the port label is already used.

        """
        if not u.position.is_neighbour(v.position):
            raise TQECException("An edge must connect two nearby nodes.")
        if self.has_edge_between(u.position, v.position):
            self._check_node_conflict(u)
            self._check_node_conflict(v)
        if u.is_port and v.is_port:
            raise TQECException("Cannot create an edge between two ports.")
        port_update: dict[str, Position3D] = {}
        if u.is_port or v.is_port:
            if port_label is None:
                raise TQECException(
                    "The edge includes a port, a port label must be provided."
                )
            if port_label in self._ports:
                raise TQECException(
                    f"There is already a port with label {port_label} in the graph."
                )
            port_update[port_label] = u.position if u.is_port else v.position
        for node in [u, v]:
            if node.is_port and len(self.edges_at(node.position)) != 0:
                raise TQECException(f"Port {node} should have at most one edge.")

        self._graph.add_node(u.position, **{_NODE_DATA_KEY: u})
        self._graph.add_node(v.position, **{_NODE_DATA_KEY: v})
        self._graph.add_edge(
            u.position, v.position, **{_EDGE_DATA_KEY: ZXEdge(u, v, has_hadamard)}
        )
        self._ports.update(port_update)

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
        """Get the edges incident to a position."""
        if position not in self:
            return []
        return [
            data[_EDGE_DATA_KEY]
            for _, _, data in self._graph.edges(position, data=True)
        ]

    def fill_ports(self, fill: Mapping[str, NodeType] | NodeType) -> None:
        """Fill the ports at specified position with a node with the given type.

        Args:
            fill: A mapping from the label of the ports to the node type to fill.

        Raises:
            TQECException: if there is no port with the given label.
            TQECException: if try to fill the port with port type.
        """
        if isinstance(fill, NodeType):
            fill = {label: fill for label in self._ports}
        for label, node_type in fill.items():
            if label not in self._ports:
                raise TQECException(f"There is no port with label {label}.")
            if node_type == NodeType.P:
                raise TQECException("Cannot fill the ports with port type.")
            pos = self._ports[label]
            self._graph.add_node(pos, **{_NODE_DATA_KEY: ZXNode(pos, node_type)})
            self._ports.pop(label)

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

    def with_zx_flipped(self, name: str | None = None) -> ZXGraph:
        """Get a new ZX graph with the node types flipped."""
        new_graph = ZXGraph(name or self.name)
        for edge in self.edges:
            u, v = edge.u.with_zx_flipped, edge.v.with_zx_flipped
            port_label = None
            if u.is_port or v.is_port:
                pos_to_label = {pos: label for label, pos in self.ports.items()}
                port_label = (
                    pos_to_label[u.position] if u.is_port else pos_to_label[v.position]
                )
            new_graph.add_edge(
                u,
                v,
                edge.has_hadamard,
                port_label,
            )
        return new_graph
