from dataclasses import dataclass
import itertools
from copy import copy
from typing import Iterable

from tqec.computation.zx_graph import ZXGraph, NodeType, ZXNode, ZXEdge
from tqec.exceptions import TQECException
from tqec.position import Position3D


@dataclass(frozen=True)
class CorrelationSurface:
    """A correlation surface in the ZX graph.

    Attributes:
        span: Either a set of correlation edges or a single node. If it is a single node,
            it represents a logical operator preserved in memory. If it is a set of edges,
            it represents the correlation between logical operators spanning in the 3D space.
        external_stabilizer: The external stabilizer of the correlation surface. External
            stabilizer is a Pauli string with the same length as the number of ports in the
            ZX graph. The Pauli operator at each port is determined by the correlation type
            of the port. It determines the correlation between the logical operators at the
            ports.

    """

    span: frozenset[ZXEdge] | ZXNode
    external_stabilizer: str

    def __post_init__(self):
        # Single node span represents a logical operator preserved in memory.
        if isinstance(self.span, ZXNode):
            if self.span.node_type not in [NodeType.X, NodeType.Z]:
                raise TQECException(
                    "The single node correlation surface must be X or Z type."
                )
        elif len(self.span) == 0:
            raise TQECException(
                "The correlation surface must contain at least one edge."
            )


def find_correlation_surfaces(
    zx_graph: ZXGraph,
) -> set[CorrelationSurface]:
    """Find the correlation surfaces in the ZX graph.

    A recursive depth-first search algorithm is used to find the correlation
    surfaces starting from each leaf node.
    """
    if not zx_graph.is_single_connected_component:
        raise TQECException(
            "The graph must be a single connected component to find the correlation surfaces."
        )
    # If the node is isolated, it is guaranteed to be X/Z type.
    # Then return a single node correlation surface.
    if zx_graph.num_nodes == 1 and zx_graph.num_edges == 0:
        return {CorrelationSurface(zx_graph.nodes[0], "")}
    # Start from each leaf node to find the correlation surfaces.
    correlation_surfaces = set()
    for leaf in zx_graph.leaf_nodes:
        correlation_surfaces.update(find_correlation_surfaces_at_leaf(zx_graph, leaf))
    return correlation_surfaces


def find_correlation_surfaces_at_leaf(
    zx_graph: ZXGraph,
    leaf: ZXNode,
) -> list[CorrelationSurface]:
    """Find the correlation surfaces starting from a leaf node in the ZX graph."""
    if leaf not in zx_graph.leaf_nodes:
        raise TQECException("The node is not a leaf node in the graph.")
    # Travese the graph to find the correlation spans.
    # Z/X type node can only support the correlation surface with the same type.
    if leaf.is_zx_node:
        spans = _find_correlation_spans_dfs(zx_graph, leaf, leaf, set())
        return _construct_compatible_correlation_surfaces(zx_graph, spans)
    x_spans = _find_correlation_spans_dfs(
        zx_graph, leaf, ZXNode(leaf.position, NodeType.X), set()
    )
    z_spans = _find_correlation_spans_dfs(
        zx_graph, leaf, ZXNode(leaf.position, NodeType.Z), set()
    )
    # Append an empty span to represent the case where there is no producted correlation.
    spans = []
    for sx, sz in itertools.product(x_spans + [frozenset()], z_spans + [frozenset()]):
        if not sx and not sz:
            continue
        # use xor to get the producted correlation.
        spans.append(sx ^ sz)
    return _construct_compatible_correlation_surfaces(zx_graph, spans)


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
        correlation_node_types = _get_nodes_correlation_types(span)
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
    correlation_types: dict[Position3D, NodeType],
) -> str:
    """Construct the external stabilizer for the correlation surface.

    The external stabilizer is a Pauli string with the same length as the number of ports
    in the ZX graph. The correlation type of each port is used to determine the Pauli
    operator in the string.
    """
    external_stabilizer = ["_"] * zx_graph.num_ports
    for i, port_label in enumerate(zx_graph.ordered_port_labels):
        port = zx_graph.ports[port_label]
        correlation_type = correlation_types.get(port)
        if correlation_type is None:
            continue
        external_stabilizer[i] = correlation_type.value
    return "".join(external_stabilizer)


def _is_compatible_correlation(
    zx_graph: ZXGraph,
    correlation_types: dict[Position3D, NodeType],
) -> bool:
    # Only need to check the leaf nodes compatibility.
    for leaf in zx_graph.leaf_nodes:
        # Port is compatible with any correlation type.
        if leaf.is_port:
            continue
        correlation_type = correlation_types.get(leaf.position)
        if correlation_type is None:
            continue
        if leaf.node_type != correlation_type:
            return False
    return True


def _get_nodes_correlation_types(
    span: frozenset[ZXEdge],
) -> dict[Position3D, NodeType]:
    correlation_types: dict[Position3D, NodeType] = {}
    for edge in span:
        for node in [edge.u, edge.v]:
            existing_type = correlation_types.get(node.position)
            if existing_type is None:
                correlation_types[node.position] = node.node_type
                continue
            cur_type = node.node_type
            product_type = _correlation_type_product(existing_type, cur_type)
            if product_type is None:
                correlation_types.pop(node.position)
            else:
                correlation_types[node.position] = product_type
    return correlation_types


def _correlation_type_product(
    type1: NodeType,
    type2: NodeType,
) -> NodeType | None:
    match type1, type2:
        case NodeType.X, NodeType.Z:
            return NodeType.Y
        case NodeType.X, NodeType.Y:
            return NodeType.Z
        case NodeType.Y, NodeType.Z:
            return NodeType.X
        case _:
            return None


def _find_correlation_spans_dfs(
    zx_graph: ZXGraph,
    parent_zx_node: ZXNode,
    parent_correlation_node: ZXNode,
    visited_positions: set[Position3D],
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
        - If the color of the node matches the correlation type, all the children
        should be traversed. Iterate through all the combinations where exactly one
        span is selected from each child, and union them to form a new span.
        Append the new span to the `correlation_spans`.
        - If the color of the node does not match the correlation type, only one
        child can be traversed. Append all the spans in the `branched_spans_from_parent`
        to the `correlation_spans`.
    """
    correlation_spans: list[frozenset[ZXEdge]] = []
    parent_position = parent_zx_node.position
    parent_zx_type = parent_zx_node.node_type
    parent_correlation_type = parent_correlation_node.node_type
    visited_positions.add(parent_position)

    branched_spans_from_parent: list[list[frozenset[ZXEdge]]] = []
    for edge in zx_graph.edges_at(parent_position):
        cur_zx_node = edge.u if edge.v == parent_zx_node else edge.v
        if cur_zx_node.position in visited_positions:
            continue
        cur_correlation_node = ZXNode(
            cur_zx_node.position,
            parent_correlation_type.with_zx_flipped()
            if edge.has_hadamard
            else parent_correlation_type,
        )
        correlation_edge = ZXEdge(
            parent_correlation_node, cur_correlation_node, edge.has_hadamard
        )
        branched_spans_from_parent.append(
            [
                span | {correlation_edge}
                for span in _find_correlation_spans_dfs(
                    zx_graph,
                    cur_zx_node,
                    cur_correlation_node,
                    copy(visited_positions),
                )
            ]
        )
    if not branched_spans_from_parent:
        return [frozenset()]
    # the color of node matches the correlation type
    # broadcast the correlation type to all the neighbors
    if parent_zx_type == parent_correlation_type:
        for prod in itertools.product(*branched_spans_from_parent):
            correlation_spans.append(frozenset(itertools.chain(*prod)))
    else:
        # the color of node does not match the correlation type
        # only one of the neighbors can be the correlation path
        correlation_spans.extend(itertools.chain(*branched_spans_from_parent))
    return correlation_spans
