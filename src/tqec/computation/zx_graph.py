"""ZX graph representation of a 3D spacetime defect diagram."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, cast

from mpl_toolkits.mplot3d.axes3d import Axes3D
import networkx as nx

from tqec.exceptions import TQECException
from tqec.position import Direction3D, Position3D

if TYPE_CHECKING:
    from tqec.computation.correlation import CorrelationSurface
    from tqec.computation.block_graph import BlockGraph


class ZXKind(Enum):
    """Valid node kind in a ZX graph."""

    X = "X"
    Y = "Y"
    Z = "Z"
    P = "PORT"  # Open port for the input/ouput of the computation

    def with_zx_flipped(self) -> ZXKind:
        if self == ZXKind.X:
            return ZXKind.Z
        elif self == ZXKind.Z:
            return ZXKind.X
        else:
            return self

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True)
class ZXNode:
    """A node in the ZX graph.

    Attributes:
        position: The 3D position of the node.
        kind: The kind of the node.
    """

    position: Position3D
    kind: ZXKind

    @property
    def is_port(self) -> bool:
        """Check if the node is an open port, i.e. represents the input/output
        of the computation."""
        return self.kind == ZXKind.P

    @property
    def is_y_node(self) -> bool:
        """Check if the node is a Y node."""
        return self.kind == ZXKind.Y

    @property
    def is_zx_node(self) -> bool:
        """Check if the node is an X or Z node."""
        return self.kind in [ZXKind.X, ZXKind.Z]

    def with_zx_flipped(self) -> ZXNode:
        """Get a new node with the ZX kind flipped."""
        return ZXNode(self.position, self.kind.with_zx_flipped())

    def __str__(self) -> str:
        return f"{self.kind}{self.position}"


@dataclass(frozen=True, order=True)
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
        if (self.u.is_y_node or self.v.is_y_node) and self.direction != Direction3D.Z:
            raise TQECException("An edge with Y kind node must be in the Z-direction.")
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

    def get_node_kind_at(self, position: Position3D) -> ZXKind:
        """Get the node kind at the given position of the edge."""
        if self.u.position == position:
            return self.u.kind
        if self.v.position == position:
            return self.v.kind
        raise TQECException("The position is not an endpoint of the edge.")

    def __str__(self) -> str:
        return f"{self.u}-{self.v}"


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
        kind: ZXKind,
    ) -> None:
        """Add a node to the graph. If the a node already exists at the position, the
        node kind will be updated.

        Note that a port or a Y node can only be added to the graph using `add_edge`
        because they must be connected to other nodes.

        Args:
            position: The 3D position of the node.
            kind: The kind of the node.

        Raises:
            TQECException: If the node kind is P or Y.
            TQECException: If a different node already exists at the position.
        """
        if kind == ZXKind.P or kind == ZXKind.Y:
            raise TQECException("Cannot add a P or Y node solely, please use add_edge.")
        node = ZXNode(position, kind)
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
        """Add an X node to the graph."""
        self.add_node(position, ZXKind.X)

    def add_z_node(self, position: Position3D) -> None:
        """Add a Z node to the graph."""
        self.add_node(position, ZXKind.Z)

    def add_edge(
        self,
        u: ZXNode,
        v: ZXNode,
        has_hadamard: bool = False,
        port_label: str | None = None,
    ) -> None:
        """Add an edge to the graph. If the nodes do not exist in the graph,
        the nodes will be created.

        A port or a Y node can only be added to the graph using this method.

        Args:
            u: The first node of the edge.
            v: The second node of the edge.
            has_hadamard: Whether the edge has a Hadamard transition.
            port_label: The label of the port, if one of the nodes is a port. Required
                if the edge includes a port.

        Raises:
            TQECException: If the edge does not connect two nearby nodes.
            TQECException: If add the edge to two ports.
            TQECException: If add the edge to a port or a Y node that already has an edge.
            TQECException: If the edge includes a port, but the port label is not provided.
            TQECException: If the edge includes a port, but the port label is already used.

        """
        if not u.position.is_neighbour(v.position):
            raise TQECException("An edge must connect two nearby nodes.")
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
            if node.kind in [ZXKind.Z, ZXKind.X]:
                continue
            if len(self.edges_at(node.position)) != 0:
                raise TQECException("Node of kind P or Y should have at most one edge.")
        edge = ZXEdge(u, v, has_hadamard)

        self._graph.add_node(u.position, **{_NODE_DATA_KEY: u})
        self._graph.add_node(v.position, **{_NODE_DATA_KEY: v})
        self._graph.add_edge(u.position, v.position, **{_EDGE_DATA_KEY: edge})
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

    def fill_ports(self, fill: Mapping[str, ZXKind] | ZXKind) -> None:
        """Fill the ports at specified position with a node with the given kind.

        Args:
            fill: A mapping from the label of the ports to the node kind to fill.

        Raises:
            TQECException: if there is no port with the given label.
            TQECException: if try to fill the port with port kind.
        """
        if isinstance(fill, ZXKind):
            fill = {label: fill for label in self._ports}
        for label, kind in fill.items():
            if label not in self._ports:
                raise TQECException(f"There is no port with label {label}.")
            if kind == ZXKind.P:
                raise TQECException("Cannot fill the ports with port kind.")
            pos = self._ports[label]
            fill_node = ZXNode(pos, kind)
            self._graph.add_node(pos, **{_NODE_DATA_KEY: fill_node})
            for edge in self.edges_at(pos):
                self._graph.remove_edge(edge.u.position, edge.v.position)
                other = edge.u if edge.v.position == pos else edge.v
                self._graph.add_edge(
                    other.position,
                    pos,
                    **{_EDGE_DATA_KEY: ZXEdge(other, fill_node, edge.has_hadamard)},
                )
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
        """Get a new ZX graph with the node kind flipped."""
        new_graph = ZXGraph(name or self.name)
        for edge in self.edges:
            u, v = edge.u.with_zx_flipped(), edge.v.with_zx_flipped()
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

    @property
    def is_single_connected_component(self) -> bool:
        """Check if the graph is a single connected component."""
        return nx.number_connected_components(self._graph) == 1

    def find_correration_surfaces(self) -> list[CorrelationSurface]:
        """Find the correlation surfaces in the ZX graph.

        A recursive depth-first search algorithm is used to find the correlation
        surfaces starting from each leaf node.
        """
        from tqec.computation.correlation import find_correlation_surfaces

        return find_correlation_surfaces(self)

    def draw(self) -> Axes3D:
        """Draw the graph using matplotlib."""
        from tqec.computation.zx_plot import plot_zx_graph

        return plot_zx_graph(self)
