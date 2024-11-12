"""Defines the :py:class:`~tqec.computation.correlation.CorrelationSurface` and
the functions to find the correlation surfaces in the ZX graph."""

from __future__ import annotations

from dataclasses import dataclass, field
import itertools
from typing import Iterable

from tqec.computation.zx_graph import ZXGraph, ZXKind, ZXNode, ZXEdge
from tqec.exceptions import TQECException
from tqec.position import Position3D


@dataclass(frozen=True)
class CorrelationSurface:
    """A record of how the logical observable moved through a computation.

    A correlation surface of a computation has close correspondence to the *spacetime stabilizer*
    in the ZX graph. A spacetime stabilizer is a Pauli product observable spread over space and
    time that when applied to the state of the computation, the state is unchanged. In the ZX
    graph, a spacetime stabilizer can be represented by a set of boundary nodes representing the
    Pauli operators and a set of edges representing the interior of the stabilizer.

    A logical observable can be moved by multiplying the spacetime stabilizers. For surface
    code, the logical operator is a 1D line. It forms a 2D surface when moving through spacetime,
    i.e the correlation surface.

    .. note::
        For more information about spacetime stabilizers, correlation surface, and their relationship,
        see `this talk <https://www.youtube.com/watch?v=1ojXEEm_JiI&t=4673s>`_ by Craig Gidney.

    Based on the above relationship, we use the term *correlation surface* and *spacetime stabilizer*
    interchangeably. We represent the correlation surface by the set of interior edges of the spacetime
    stabilizer in the ZX graph. Each edge can be seen as a decomposed spacetime stabilizer which has
    Pauli operator specified by the node kinds at the two ends of the edge. For example, an edge
    connecting two X nodes represents a local ``XX`` spacetime stabilizer. There is also a special kind of
    correlation surface that has no interior edges but represented by a single node. It can be seen as
    applying spider fusion rule to a single edge ZX graph, which results in a correlation surface totally
    compressed in a single node.

    Additionally, we represent the boundary nodes of the spacetime stabilizer by :py:attr:`~tqec.computation.correlation.CorrelationSurface.external_stabilizer`,
    which is a mapping from the input/output labels to the Pauli operator at the port. If the ZX graph is closed,
    i.e. there is no open port, that means that the stabilizer is terminated with the initialization or
    measurements so has no external stabilizer.


    Attributes:
        nodes: A set of ``ZXNode`` representing the nodes appeared in the correlation surface. The kind of
            the node is determined by which type of logical observable the node supports in the
            correlation surface. For example, if either a logical X observable or Z observable has been
            moved through the node position, then the node is of X or Z kind. If both X and Z observable
            have been moved through the node position, the node is of Y kind.
        span: A set of ``ZXEdge`` representing the span of the correlation surface in spacetime, i.e. the movement
            of the logical observable.
        external_stabilizer: A mapping from the port label to the Pauli operator at the port, which
            represents the boundary nodes of the spacetime stabilizer. Sign of the stabilizer is neglected.
            If the ZX graph is closed, i.e. there is no open port, the stabilizer is terminated with the
            initialization or measurements so has no external stabilizer.
    """

    nodes: frozenset[ZXNode]
    span: frozenset[ZXEdge] = frozenset()
    external_stabilizer: dict[str, str] = field(
        default_factory=dict, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        if len(self.nodes) == 0:
            raise TQECException(
                "The correlation surface must contain at least one node."
            )
        if any(not node.is_zx_node for edge in self.span for node in edge):
            raise TQECException(
                "The edges in the correlation surface must be between Z/X type nodes.",
            )

    @staticmethod
    def from_span(zx_graph: ZXGraph, span: Iterable[ZXEdge]) -> CorrelationSurface:
        """Construct a correlation surface from the set of edges representing
        the span of the correlation surface.

        Args:
            zx_graph: The ZX graph where the correlation surface is extracted.
            span: The set of edges representing the span of the correlation surface.

        Returns:
            A :py:class:`~tqec.computation.correlation.CorrelationSurface` object.
        """
        span = frozenset(span)

        supported_observables = CorrelationSurface._get_supported_observable_at_nodes(
            span
        )
        nodes = frozenset(
            ZXNode(pos, kind) for pos, kind in supported_observables.items()
        )

        external_stabilizer = {}
        for label, port in zx_graph.ports.items():
            observable_type = supported_observables.get(port)
            if observable_type is None:
                external_stabilizer[label] = "I"
            else:
                external_stabilizer[label] = observable_type.value
        return CorrelationSurface(nodes, span, external_stabilizer)

    @staticmethod
    def _get_supported_observable_at_nodes(
        span: Iterable[ZXEdge],
    ) -> dict[Position3D, ZXKind]:
        """Get the supported observable type at each node in the correlation
        surface."""
        observables_appeared: dict[Position3D, set[ZXKind]] = {}
        for edge in span:
            for node in edge:
                observables_appeared.setdefault(node.position, set()).add(node.kind)

        supported_observables: dict[Position3D, ZXKind] = {}
        for pos, types in observables_appeared.items():
            if len(types) == 1:
                supported_observables[pos] = types.pop()
            else:
                assert len(types) == 2
                supported_observables[pos] = ZXKind.Y
        return supported_observables

    @property
    def observables_at_nodes(self) -> dict[Position3D, ZXKind]:
        """A mapping from the position of the node to the logical observable
        type that the node supports in the correlation surface."""
        return {node.position: node.kind for node in self.nodes}

    @property
    def has_single_node(self) -> bool:
        """Whether the correlation surface contains only a single node."""
        return len(self.nodes) == 1


def find_correlation_surfaces(
    zx_graph: ZXGraph,
) -> list[CorrelationSurface]:
    """Find all the
    :py:class:`~tqec.computation.correlation.CorrelationSurface` in a ZX graph.

    Starting from each leaf node in the graph, the function explores how can the X/Z logical observable
    move through the graph to form a correlation surface:

    - For a X/Z kind leaf node, it can only support the logical observable with the opposite type. Only
      a single type of logical observable is explored from the leaf node.
    - For a Y kind leaf node, it can only support the Y logical observable, i.e. the presence of
      both X and Z logical observable. Both X and Z type logical observable are explored from the leaf node.
      And the two correlation surfaces are combined to form the Y type correlation surface.
    - For the port node, it can support any type of logical observable. Both X and Z type logical observable
      are explored from the port node.

    The function uses a flood fill like recursive algorithm to find the correlation surface in the graph.
    Firstly, we define two types of nodes in the graph:

    - *broadcast node:* A node that has seen logical observable with basis opposite to its own basis.
      A logical observable needs to be broadcasted to all the neighbors of the node.
    - *passthrough node:* A node that has seen logical observable with the same basis as its own basis.
      A logical observable needs to be only supported on an even number of edges connected to the node.

    The algorithm starts from a set of frontier nodes and greedily expands the correlation
    surface until no more broadcast nodes are in the frontier. Then it explore the
    passthrough nodes, and select even number of edges to be included in the surface. If
    no such selection can be made, the search is pruned. For different choices, the algorithm
    recursively explores the next frontier until the search is completed. Finally, the branches
    at different nodes are produced to form the correlation surface.

    Args:
        zx_graph: The ZX graph to find the correlation surfaces.

    Returns:
        A list of `CorrelationSurface` in the graph.

    Raises:
        TQECException: If the graph does not contain any leaf node.
    """
    zx_graph.check_invariants()
    # Edge case: single node graph
    if zx_graph.num_nodes == 1:
        return [
            CorrelationSurface(nodes=frozenset({zx_graph.nodes[0].with_zx_flipped()}))
        ]
    # Find correlation surfaces starting from each leaf node
    leaves = set(zx_graph.leaf_nodes)
    if not leaves:
        raise TQECException(
            "The graph must contain at least one leaf node to find correlation surfaces."
        )
    correlation_surfaces: set[CorrelationSurface] = set()
    for leaf in leaves:
        correlation_surfaces.update(
            _find_correlation_surfaces_from_leaf(zx_graph, leaf)
        )
    # sort the correlation surfaces to make the result deterministic
    return sorted(correlation_surfaces, key=lambda x: sorted(x.span))


def _find_correlation_surfaces_from_leaf(
    zx_graph: ZXGraph,
    leaf: ZXNode,
) -> list[CorrelationSurface]:
    """Find the correlation surfaces starting from a leaf node in the ZX
    graph."""
    # Z/X type node can only support the correlation surface with the opposite type.
    if leaf.is_zx_node:
        spans = (
            _find_spans_with_flood_fill(zx_graph, {leaf.with_zx_flipped()}, set()) or []
        )
        return _construct_compatible_correlation_surfaces(zx_graph, spans)
    x_spans = (
        _find_spans_with_flood_fill(zx_graph, {ZXNode(leaf.position, ZXKind.X)}, set())
        or []
    )
    z_spans = (
        _find_spans_with_flood_fill(zx_graph, {ZXNode(leaf.position, ZXKind.Z)}, set())
        or []
    )
    # For the port node, try to construct both the x and z type correlation surfaces.
    if leaf.is_port:
        return _construct_compatible_correlation_surfaces(zx_graph, x_spans + z_spans)
    # For the Y type node, the correlation surface must be the product of the x and z type.
    assert leaf.is_y_node
    return _construct_compatible_correlation_surfaces(
        zx_graph, [sx | sz for sx, sz in itertools.product(x_spans, z_spans)]
    )


def _construct_compatible_correlation_surfaces(
    zx_graph: ZXGraph,
    spans: Iterable[frozenset[ZXEdge]],
) -> list[CorrelationSurface]:
    """From the spans, construct the correlation surfaces that are compatible
    with the ZX graph.

    The compatibility is determined by comparing the logical observable basis
    and the node kind for the leaf nodes in the graph:

    - The Z/X observable must be supported on the opposite type node.
    - The Y observable can only be supported on the Y type node.
    - The port node can support any type of logical observable.
    """
    correlation_surfaces = []

    def _is_compatible(
        supported_observables: dict[Position3D, ZXKind],
    ) -> bool:
        # Check the leaf nodes compatibility.
        for leaf in zx_graph.leaf_nodes:
            # Port is compatible with any correlation type.
            if leaf.is_port:
                continue
            observable_basis = supported_observables.get(leaf.position)
            if observable_basis is None:
                continue
            # Y correlation can only be supported on the Y type node.
            if (observable_basis == ZXKind.Y) ^ (leaf.kind == ZXKind.Y):
                return False
            # Z/X correlation must be supported on the opposite type node.
            if observable_basis != ZXKind.Y and observable_basis == leaf.kind:
                return False
        return True

    for span in spans:
        if not span:
            continue
        correlation_surface = CorrelationSurface.from_span(zx_graph, span)
        if not _is_compatible(correlation_surface.observables_at_nodes):
            continue
        correlation_surfaces.append(correlation_surface)
    return correlation_surfaces


def _find_spans_with_flood_fill(
    zx_graph: ZXGraph,
    frontier: set[ZXNode],
    current_span: set[ZXEdge],
) -> list[frozenset[ZXEdge]] | None:
    """Find the correlation spans in the ZX graph using the flood fill like
    algorithm."""
    # The ZX node kind mismatches the logical observable basis, then we can flood
    # through(broadcast) all the edges connected to the current node.
    # Greedily flood through the edges until encountering the passthrough node.
    broadcast_nodes = {n for n in frontier if not _match_at(zx_graph, n)}
    while broadcast_nodes:
        correlation_node = broadcast_nodes.pop()
        frontier.remove(correlation_node)
        for correlation_edge in _get_correlation_edges_at(zx_graph, correlation_node):
            if correlation_edge in current_span:
                continue
            u, v = correlation_edge
            next_correlation_node = u if v == correlation_node else v
            frontier.add(next_correlation_node)
            current_span.add(correlation_edge)
            if not _match_at(zx_graph, next_correlation_node):
                broadcast_nodes.add(next_correlation_node)

    if not frontier:
        return [frozenset(current_span)]

    # The node kind matches the observable basis, enforce the parity to be even.
    # There are different choices of the edges to be included in the span.

    # Each list entry represents the possible branches at a node.
    # Each tuple in the list entry represents a branch, where the first element is the
    # nodes to be included in the branch's frontier, and the second element is the edges
    # to be included in the branch's span.
    branches_at_different_nodes: list[list[tuple[set[ZXNode], set[ZXEdge]]]] = []
    for correlation_node in set(frontier):
        assert _match_at(zx_graph, correlation_node)
        frontier.remove(correlation_node)

        correlation_edges = _get_correlation_edges_at(zx_graph, correlation_node)
        edges_in_span = correlation_edges & current_span
        edges_left = correlation_edges - current_span
        parity = len(edges_in_span) % 2
        # Cannot fulfill the parity requirement, prune the search
        if parity == 1 and not edges_left:
            return None
        # starts from a node that only has a single edge
        if parity == 0 and not edges_in_span and len(edges_left) <= 1:
            return None
        branches_at_node: list[tuple[set[ZXNode], set[ZXEdge]]] = []
        for n in range(parity, len(edges_left) + 1, 2):
            for branch_edges in itertools.combinations(edges_left, n):
                branches_at_node.append(
                    (
                        {e.u if e.u != correlation_node else e.v for e in branch_edges},
                        set(branch_edges),
                    )
                )
        branches_at_different_nodes.append(branches_at_node)

    assert branches_at_different_nodes, "Should not be empty."

    final_spans: list[frozenset[ZXEdge]] = []
    # Product of the branches at different nodes together
    for product in itertools.product(*branches_at_different_nodes):
        product_frontier = set(frontier)
        product_span = set(current_span)
        for nodes, edges in product:
            product_frontier.update(nodes)
            product_span.update(edges)
        spans = _find_spans_with_flood_fill(zx_graph, product_frontier, product_span)
        if spans is not None:
            final_spans.extend(spans)
    return final_spans or None


def _get_correlation_edges_at(
    zx_graph: ZXGraph,
    correlation_node: ZXNode,
) -> set[ZXEdge]:
    correlation_edges: set[ZXEdge] = set()
    zx_node = zx_graph[correlation_node.position]
    for zx_edge in set(zx_graph.edges_at(correlation_node.position)):
        next_zx_node = zx_edge.u if zx_edge.v == zx_node else zx_edge.v
        next_correlation_kind = (
            correlation_node.kind.with_zx_flipped()
            if zx_edge.has_hadamard
            else correlation_node.kind
        )
        next_correlation_node = ZXNode(next_zx_node.position, next_correlation_kind)
        correlation_edges.add(
            ZXEdge(correlation_node, next_correlation_node, zx_edge.has_hadamard)
        )
    return correlation_edges


def _match_at(zx_graph: ZXGraph, correlation_node: ZXNode) -> bool:
    zx_node = zx_graph[correlation_node.position]
    return zx_node.kind == correlation_node.kind
