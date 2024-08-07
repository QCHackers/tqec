"""ZX graph representation of a 3D spacetime defect diagram."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from enum import Enum
from dataclasses import dataclass, astuple

import networkx as nx
import numpy as np

from tqec.position import Position3D, Direction3D
from tqec.exceptions import TQECException

if TYPE_CHECKING:
    from tqec.sketchup.block_graph import BlockGraph


class NodeType(Enum):
    """Valid node types in a ZX graph."""

    X = "x"  # X-type node
    Z = "z"  # Z-type node
    V = "v"  # Virtual node that represents an open port


@dataclass(frozen=True)
class ZXNode:
    position: Position3D
    node_type: NodeType

    @property
    def is_virtual(self) -> bool:
        """Check if the node is virtual."""
        return self.node_type == NodeType.V


@dataclass(frozen=True)
class ZXEdge:
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
        """Get the direction of the edge."""
        u, v = self.u.position, self.v.position
        if u.x != v.x:
            return Direction3D.X
        if u.y != v.y:
            return Direction3D.Y
        return Direction3D.Z


_NODE_DATA_KEY = "tqec_zx_node_data"
_EDGE_DATA_KEY = "tqec_zx_edge_data"


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
        self._graph.add_node(position, **{_NODE_DATA_KEY: ZXNode(position, node_type)})

    def add_z_node(self, position: Position3D) -> None:
        """Add a Z-type node to the graph."""
        self.add_node(position, NodeType.Z)

    def add_x_node(self, position: Position3D) -> None:
        """Add an X-type node to the graph."""
        self.add_node(position, NodeType.X)

    def add_virtual_node(self, position: Position3D) -> None:
        """Add a virtual node to the graph."""
        self.add_node(position, NodeType.V)

    def add_edge(
        self,
        u: Position3D,
        v: Position3D,
        has_hadamard: bool = False,
    ) -> None:
        """Add an edge to the graph.

        Args:
            u: The position of the first node.
            v: The position of the second node.
            has_hadamard: Whether the edge has a Hadamard transition.
        """
        if u not in self._graph or v not in self._graph:
            raise TQECException("Both nodes must exist in the graph.")
        u_node: ZXNode = self._graph.nodes[u][_NODE_DATA_KEY]
        v_node: ZXNode = self._graph.nodes[v][_NODE_DATA_KEY]
        self._graph.add_edge(
            u, v, **{_EDGE_DATA_KEY: ZXEdge(u_node, v_node, has_hadamard)}
        )

    def get_node(self, position: Position3D) -> ZXNode | None:
        """Get the node by position."""
        if position not in self._graph:
            return None
        return cast(ZXNode, self._graph.nodes[position][_NODE_DATA_KEY])

    def get_edge(self, u: Position3D, v: Position3D) -> ZXEdge | None:
        """Get the edge by its endpoint positions."""
        if not self._graph.has_edge(u, v):
            return None
        return cast(ZXEdge, self._graph.edges[u, v][_EDGE_DATA_KEY])

    def edges_at(self, position: Position3D) -> list[ZXEdge]:
        """Get the edges incident to a node."""
        return [
            data[_EDGE_DATA_KEY]
            for _, _, data in self._graph.edges(position, data=True)
        ]

    def draw(self, show_title: bool = True) -> None:
        """Draw the 3D graph using matplotlib."""
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.axes3d import Axes3D

        fig = plt.figure()
        # See https://matplotlib.org/stable/users/explain/toolkits/mplot3d.html
        ax = cast(Axes3D, fig.add_subplot(111, projection="3d"))

        node_positions = np.array(
            [astuple(node.position) for node in self.nodes if not node.is_virtual]
        ).T
        edge_positions = np.array(
            [
                (astuple(edge.u.position), astuple(edge.v.position))
                for edge in self.edges
            ]
        )
        hadamard_edges = np.array(
            [
                edge_positions[i]
                for i, edge in enumerate(self.edges)
                if edge.has_hadamard
            ],
        )
        has_hadamard = hadamard_edges.size > 0
        if has_hadamard:
            hadamard_position = np.mean(hadamard_edges, axis=1).T

        ax.scatter(
            *node_positions,
            s=400,
            c=[
                "black" if n.node_type == NodeType.X else "white"
                for n in self.nodes
                if not n.is_virtual
            ],
            alpha=1.0,
            edgecolors="black",
        )

        for edge in edge_positions:
            ax.plot(*edge.T, color="tab:gray")

        if has_hadamard:
            # use yellow square to indicate Hadamard transition
            ax.scatter(
                *hadamard_position,
                s=200,
                c="yellow",
                alpha=1.0,
                edgecolors="black",
                marker="s",
            )

        ax.grid(False)
        for dim in (ax.xaxis, ax.yaxis, ax.zaxis):
            dim.set_ticks([])
        x_limits, y_limits, z_limits = ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()

        plot_radius = 0.5 * max(
            abs(limits[1] - limits[0]) for limits in [x_limits, y_limits, z_limits]
        )

        ax.set_xlim3d(
            [np.mean(x_limits) - plot_radius, np.mean(x_limits) + plot_radius]
        )
        ax.set_ylim3d(
            [np.mean(y_limits) - plot_radius, np.mean(y_limits) + plot_radius]
        )
        ax.set_zlim3d(
            [np.mean(z_limits) - plot_radius, np.mean(z_limits) + plot_radius]
        )
        if show_title:
            ax.set_title(self.name)

        fig.tight_layout()
        plt.show()

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
        from tqec.sketchup.block_graph import BlockGraph

        return BlockGraph.from_zx_graph(self, name=name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ZXGraph):
            return False
        return cast(bool, nx.utils.graphs_equal(self._graph, other._graph))
