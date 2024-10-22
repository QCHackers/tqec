from dataclasses import dataclass
import functools
import itertools
from copy import copy
from typing import Iterable

from tqec.computation.zx_graph import ZXGraph, ZXKind, ZXNode, ZXEdge
from tqec.exceptions import TQECException
from tqec.position import Position3D


@dataclass(frozen=True, order=True)
class CorrelationSurface:
    """A correlation surface in the ZX graph.

    Attributes:
        span: Either a set of correlation edges or a single node. If it is a single node,
            it represents a logical operator preserved in memory. If it is a set of edges,
            it represents the correlation between logical operators spanning in the 3D space.
        external_stabilizer: The external stabilizer of the correlation surface. The external
            stabilizer is a mapping from the port label to the Pauli operator at the port.
            Sign of the stabilizer is neglected.

    """

    span: frozenset[ZXEdge] | ZXNode
    external_stabilizer: dict[str, str]

    def __post_init__(self):
        # Single node span represents a logical operator preserved in memory.
        if isinstance(self.span, ZXNode):
            if self.span.kind not in [ZXKind.X, ZXKind.Z]:
                raise TQECException(
                    "The single node correlation surface must be X or Z type."
                )
        elif len(self.span) == 0:
            raise TQECException(
                "The correlation surface must contain at least one edge."
            )

    def __hash__(self):
        return hash(self.span)

    def get_node_correlation_types(self) -> dict[Position3D, ZXKind]:
        """Get the correlation type of the nodes in the correlation surface.

        Returns:
            A dictionary mapping the position of the node to the correlation type.
        """
        if isinstance(self.span, ZXNode):
            return {self.span.position: self.span.kind}
        return _get_node_correlation_types(self.span)


def find_correlation_surfaces(
    zx_graph: ZXGraph,
) -> list[CorrelationSurface]:
    """Find the correlation surfaces in the ZX graph.

    A recursive depth-first search algorithm is used to find the correlation
    surfaces starting from each leaf node or internal Y node.
    """
    zx_graph.validate()
    # If the node is isolated, it is guaranteed to be X/Z type.
    # Then return a single node correlation surface.
    if zx_graph.num_nodes == 1 and zx_graph.num_edges == 0:
        return [CorrelationSurface(zx_graph.nodes[0].with_zx_flipped(), {})]
    # Start from each leaf node or internal Y node to find the correlation surfaces.
    roots = set(zx_graph.leaf_nodes)
    roots.update(node for node in zx_graph.nodes if node.is_y_node)
    correlation_surfaces = set()
    for root in roots:
        correlation_surfaces.update(find_correlation_surfaces_from(zx_graph, root))
    return sorted(correlation_surfaces)


def find_correlation_surfaces_from(
    zx_graph: ZXGraph,
    root: ZXNode,
) -> list[CorrelationSurface]:
    """Find the correlation surfaces starting from a specific node in the ZX graph."""
    if root not in zx_graph.leaf_nodes and not root.is_y_node:
        raise TQECException("The root node must be a leaf node or an internal Y node.")
    # Traverse the graph to find the correlation spans.
    # Z/X type node can only support the correlation surface with the same type.
    if root.is_zx_node:
        spans = _find_correlation_spans_dfs(
            zx_graph, root, root.with_zx_flipped(), set()
        )
        return _construct_compatible_correlation_surfaces(zx_graph, spans)
    x_spans = _find_correlation_spans_dfs(
        zx_graph, root, ZXNode(root.position, ZXKind.X), set()
    )
    z_spans = _find_correlation_spans_dfs(
        zx_graph, root, ZXNode(root.position, ZXKind.Z), set()
    )
    # For the port node, try to construct both the x and z type correlation surfaces.
    if root.is_port:
        return _construct_compatible_correlation_surfaces(zx_graph, x_spans + z_spans)
    # For the Y type node, the correlation surface must be the product of the x and z type.
    assert root.is_y_node
    correlation_surfaces = []
    for edge in sorted(zx_graph.edges_at(root.position)):
        u, v = edge.u, edge.v
        child = u if v == root else v
        x_correlation = ZXNode(
            child.position, ZXKind.Z if edge.has_hadamard else ZXKind.X
        )
        x_correlation_edge = ZXEdge(
            ZXNode(root.position, ZXKind.X),
            x_correlation,
            edge.has_hadamard,
        )
        x_spans = _find_correlation_spans_dfs(
            zx_graph,
            child,
            x_correlation,
            {root.position},
            frozenset([x_correlation_edge]),
        )
        z_spans = _find_correlation_spans_dfs(
            zx_graph,
            child,
            x_correlation.with_zx_flipped(),
            {root.position},
            frozenset([x_correlation_edge.with_zx_flipped()]),
        )

        correlation_surfaces.extend(
            _construct_compatible_correlation_surfaces(
                zx_graph, [sx | sz for sx, sz in itertools.product(x_spans, z_spans)]
            )
        )
    return correlation_surfaces


def _construct_compatible_correlation_surfaces(
    zx_graph: ZXGraph,
    spans: Iterable[frozenset[ZXEdge]],
) -> list[CorrelationSurface]:
    """From the correlation spans, construct the correlation surfaces that are compatible
    with the ZX graph.

    The compatibility is determined by comparing the correlation type and the node type
    of the leaf nodes in the graph. If the node type is not P, the correlation type must
    be the same as the node type. If the node type is P, the correlation type can be any
    type.
    """
    correlation_surfaces = []
    for span in spans:
        if not span:
            continue
        correlation_node_types = _get_node_correlation_types(span)
        if not _is_compatible_correlation(zx_graph, correlation_node_types):
            continue
        correlation_surfaces.append(
            CorrelationSurface(
                span,
                _get_external_stabilizer(zx_graph, correlation_node_types),
            )
        )
    return correlation_surfaces


def _get_external_stabilizer(
    zx_graph: ZXGraph,
    correlation_types: dict[Position3D, ZXKind],
) -> dict[str, str]:
    """Construct the external stabilizer for the correlation surface.

    The external stabilizer is a mapping from the port label to the Pauli operator
    at the port.
    """
    external_stabilizer = {}
    for label, port in zx_graph.ports.items():
        correlation_type = correlation_types.get(port)
        if correlation_type is None:
            external_stabilizer[label] = "I"
        else:
            external_stabilizer[label] = correlation_type.value
    return external_stabilizer


def _is_compatible_correlation(
    zx_graph: ZXGraph,
    correlation_types: dict[Position3D, ZXKind],
) -> bool:
    # Check the leaf nodes compatibility.
    for leaf in zx_graph.leaf_nodes:
        # Port is compatible with any correlation type.
        # And leave the Y type nodes to be handled later.
        if leaf.is_port or leaf.is_y_node:
            continue
        correlation_type = correlation_types.get(leaf.position)
        if correlation_type is None:
            continue
        # Y correlation cannot be supported by Z/X type node.
        # Z/X correlation must be supported on the opposite type node.
        if correlation_type == ZXKind.Y or correlation_type == leaf.kind:
            return False
    # Check for Y nodes
    for node in zx_graph.nodes:
        if not node.is_y_node:
            continue
        for edge in zx_graph.edges_at(node.position):
            for n in edge:
                correlation = correlation_types.get(n.position)
                if correlation is None:
                    continue
                if correlation != ZXKind.Y:
                    return False
    return True


def _get_node_correlation_types(
    span: frozenset[ZXEdge],
) -> dict[Position3D, ZXKind]:
    correlations_at_position: dict[Position3D, set[ZXKind | None]] = {}
    for edge in span:
        for node in edge:
            correlations_at_position.setdefault(node.position, {None}).add(node.kind)

    correlation_types: dict[Position3D, ZXKind] = {}
    for pos, types in correlations_at_position.items():
        product = functools.reduce(_correlation_type_product, types)
        if product is not None:
            correlation_types[pos] = product
    return correlation_types


def _correlation_type_product(
    type1: ZXKind | None,
    type2: ZXKind | None,
) -> ZXKind | None:
    if type1 is None:
        return type2
    if type2 is None:
        return type1
    type_set = {type1, type2}
    if type_set == {ZXKind.X, ZXKind.Z}:
        return ZXKind.Y
    if type_set == {ZXKind.X, ZXKind.Y}:
        return ZXKind.Z
    if type_set == {ZXKind.Y, ZXKind.Z}:
        return ZXKind.X
    return None


def _find_correlation_spans_dfs(
    zx_graph: ZXGraph,
    parent_zx_node: ZXNode,
    parent_correlation_node: ZXNode,
    visited_positions: set[Position3D],
    previous_edges: frozenset[ZXEdge] = frozenset(),
) -> list[frozenset[ZXEdge]]:
    """Recursively find all the correlation spans starting from a node,
    represented by the correlation edges in the subgraph.

    The algorithm is as follows:
    1. Initialization
        - Initialize the `correlation_spans` as an empty list.
        - Add the parent to the `visited_positions`.
        - Initialize a list `branched_spans_from_parent` to hold subgraphs constructed
        from the neighbors of the parent.
    2. Iterate through all edges connected to parent. For each edge:
        - If the child node is already visited, skip the edge.
        - Determine the correlation type of the child node based on the correlation
        type of the parent and the Hadamard transition.
        - Create a new correlation node for the child and the correlation edge
        between the parent and the child.
        - Recursively call this method to find the correlation spans starting
        from the child. Then add the edge in the last step to each of the spans.
        Append the spans to the `branched_spans_from_parent`.
    3. Post-processing
        - If no spans are found, return a single empty span.
        - If the color of the node does not match the correlation type, all the children
        should be traversed. Iterate through all the combinations where exactly one span
        is selected from each child, and union them to form a new span. Append the new
        span to the `correlation_spans`.
        - If the color of the node matches the correlation type, only one child can be
        traversed. Append all the spans in the `branched_spans_from_parent` to the
        `correlation_spans`.
    """
    correlation_spans: list[frozenset[ZXEdge]] = []
    parent_position = parent_zx_node.position
    parent_zx_kind = parent_zx_node.kind
    parent_correlation = parent_correlation_node.kind
    visited_positions.add(parent_position)

    branched_spans_from_parent: list[list[frozenset[ZXEdge]]] = []
    for edge in zx_graph.edges_at(parent_position):
        cur_zx_node = edge.u if edge.v == parent_zx_node else edge.v
        if cur_zx_node.position in visited_positions and not cur_zx_node.is_y_node:
            continue
        cur_correlation_node = ZXNode(
            cur_zx_node.position,
            parent_correlation.with_zx_flipped()
            if edge.has_hadamard
            else parent_correlation,
        )
        correlation_edge = ZXEdge(
            parent_correlation_node, cur_correlation_node, edge.has_hadamard
        )
        if cur_zx_node.is_y_node:
            branched_spans_from_parent.append([frozenset([correlation_edge])])
            continue

        branched_spans_from_parent.append(
            _find_correlation_spans_dfs(
                zx_graph,
                cur_zx_node,
                cur_correlation_node,
                copy(visited_positions),
                frozenset([correlation_edge]),
            )
        )
    if not branched_spans_from_parent:
        return [previous_edges]
    # the color of node does not match the correlation type
    # broadcast the correlation type to all the neighbors
    if parent_zx_kind != ZXKind.Y and parent_zx_kind != parent_correlation:
        for prod in itertools.product(*branched_spans_from_parent):
            correlation_spans.append(frozenset(itertools.chain(*prod)) | previous_edges)
    else:
        # the color of node match the correlation type or the node is Y type
        # only one of the neighbors can be the correlation path
        correlation_spans.extend(
            [
                span | previous_edges
                for span in itertools.chain(*branched_spans_from_parent)
            ]
        )
    return correlation_spans
