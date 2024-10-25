"""ZX graph representation of a 3D spacetime defect diagram."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Generator, cast

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

    def __lt__(self, other: ZXKind) -> bool:
        return self.value < other.value


@dataclass(frozen=True, order=True)
class ZXNode:
    """A node in the ZX graph.

    Attributes:
        position: The 3D position of the node.
        kind: The kind of the node.
    """

    position: Position3D
    kind: ZXKind
    label: str | None = None

    def __post_init__(self) -> None:
        if self.kind == ZXKind.P and self.label is None:
            raise TQECException("A port node must have a port label.")

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
        return ZXNode(self.position, self.kind.with_zx_flipped(), self.label)

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

    def __iter__(self) -> Generator[ZXNode]:
        yield self.u
        yield self.v

    def __str__(self) -> str:
        strs = [str(self.u), str(self.v)]
        if self.has_hadamard:
            strs.insert(1, "H")
        return "-".join(strs)

    def with_zx_flipped(self) -> ZXEdge:
        """Get a new edge with the node kind flipped."""
        return ZXEdge(
            self.u.with_zx_flipped(), self.v.with_zx_flipped(), self.has_hadamard
        )


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
        """The number of nodes in the graph."""
        return cast(int, self._graph.number_of_nodes())

    @property
    def num_ports(self) -> int:
        """The number of open ports in the graph."""
        return len(self._ports)

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
        return [node for node in self.nodes if self.node_degree(node) == 1]

    @property
    def ports(self) -> dict[str, Position3D]:
        """Get the position of open ports of the graph."""
        return self._ports

    def node_degree(self, node: ZXNode) -> int:
        return self._graph.degree(node.position)  # type: ignore

    def add_node(
        self,
        position: Position3D,
        kind: ZXKind,
        label: str | None = None,
        check_conflict: bool = True,
    ) -> None:
        """Add a node to the graph. If a node already exists at the position, the
        node kind will be updated.

        Args:
            position: The 3D position of the node.
            kind: The kind of the node.
            label: The label of the port node if the node is a port.
            check_conflict: Whether to check for node conflict.

        Raises:
            TQECException: If a different node already exists at the position.
            TQECException: If the port label is already used.
        """
        node = ZXNode(position, kind, label)
        if check_conflict:
            self._check_node_conflict(node)
        self._graph.add_node(position, **{_NODE_DATA_KEY: node})
        if node.is_port:
            assert node.label is not None, "A port node is guaranteed to have a label."
            self._ports[node.label] = position

    def _check_node_conflict(self, node: ZXNode) -> None:
        """Check whether a new node can be added to the graph without conflict."""
        position = node.position
        if position in self:
            if self[position] == node:
                return
            raise TQECException(
                f"The graph already has a different node {self[position]} at this position."
            )
        if node.is_port and node.label in self._ports:
            raise TQECException(
                f"There is already a different port with label {node.label} in the graph."
            )

    def add_edge(
        self,
        u: ZXNode,
        v: ZXNode,
        has_hadamard: bool = False,
    ) -> None:
        """Add an edge to the graph. If the nodes do not exist in the graph,
        the nodes will be created.

        Args:
            u: The first node of the edge.
            v: The second node of the edge.
            has_hadamard: Whether the edge has a Hadamard transition.

        """
        edge = ZXEdge(u, v, has_hadamard)
        # Check before adding the nodes to avoid rolling back the changes
        self._check_node_conflict(u)
        self._check_node_conflict(v)
        self.add_node(u.position, u.kind, u.label, check_conflict=False)
        self.add_node(v.position, v.kind, v.label, check_conflict=False)
        self._graph.add_edge(u.position, v.position, **{_EDGE_DATA_KEY: edge})

    def has_edge_between(self, pos1: Position3D, pos2: Position3D) -> bool:
        """Check if there is an edge between two positions."""
        return cast(bool, self._graph.has_edge(pos1, pos2))

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
            # Overwrite the node at the port position
            self._graph.add_node(pos, **{_NODE_DATA_KEY: fill_node})
            for edge in self.edges_at(pos):
                self._graph.remove_edge(edge.u.position, edge.v.position)
                other = edge.u if edge.v.position == pos else edge.v
                self._graph.add_edge(
                    other.position,
                    pos,
                    **{_EDGE_DATA_KEY: ZXEdge(other, fill_node, edge.has_hadamard)},
                )
            # Delete the port label
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
        from tqec.computation.conversion import (
            convert_zx_graph_to_block_graph,
        )

        return convert_zx_graph_to_block_graph(self, name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ZXGraph):
            return False
        return (
            cast(bool, nx.utils.graphs_equal(self._graph, other._graph))
            and self._ports == other._ports
        )

    def __contains__(self, position: Position3D) -> bool:
        return position in self._graph

    def __getitem__(self, position: Position3D) -> ZXNode:
        return cast(ZXNode, self._graph.nodes[position][_NODE_DATA_KEY])

    def with_zx_flipped(self, name: str | None = None) -> ZXGraph:
        """Get a new ZX graph with the node kind flipped."""
        flipped = ZXGraph(name or self.name)
        for edge in self.edges:
            u, v = edge.u.with_zx_flipped(), edge.v.with_zx_flipped()
            flipped.add_edge(u, v, edge.has_hadamard)
        return flipped

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

    def validate(self) -> None:
        """Check the validity of the graph to represent a computation.
        This method performs a necessary but not sufficient check.

        To represent a valid computation, the graph must have:
            - the graph is a single connected component
            - the graph has no 3D corner
            - the port node is a leaf node
            - Y nodes is a leaf node and is time-like, i.e. only have Z-direction edges

        Raises:
            TQECException: If the graph is not a single connected component.
            TQECException: If the port node is not a leaf node.
            TQECException: If the Y node is not a leaf node.
            TQECException: If the Y node has an edge not in Z direction.
        """
        if nx.number_connected_components(self._graph) != 1:
            raise TQECException(
                "The graph must be a single connected component to represent a computation."
            )

        for node in self.nodes:
            if len({e.direction for e in self.edges_at(node.position)}) == 3:
                raise TQECException(f"ZX graph has a 3D corner at {node.position}.")
            if not node.is_zx_node and self.node_degree(node) != 1:
                raise TQECException("The port/Y node must be a leaf node.")
            if node.is_y_node:
                (edge,) = self.edges_at(node.position)
                if not edge.direction == Direction3D.Z:
                    raise TQECException("The Y node must only has Z-direction edge.")
