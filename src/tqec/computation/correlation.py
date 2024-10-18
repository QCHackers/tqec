import itertools
from copy import copy

from tqec.computation.zx_graph import ZXGraph, NodeType, ZXNode, ZXEdge
from tqec.position import Position3D


def _find_correlation_subgraphs_dfs(
    zx_graph: ZXGraph,
    parent_corr_node: ZXNode,
    parent_zx_node_type: NodeType,
    visited_positions: set[Position3D],
) -> list[set[ZXEdge]]:
    """Recursively find all the correlation subgraphs starting from a node,
    represented by the correlation edges in the subgraph.

    The algorithm is as follows:
    1. Initialization
        - Initialize the `correlation_subgraphs` as an empty list.
        - Add the parent to the `visited_positions`.
        - Initialize a list `branched_subgraph` to hold subgraphs constructed
        from the neighbors of the parent.
    2. Iterate through all edges connected to parent. For each edge:
        - If the child node is already visited, skip the edge.
        - Determine the correlation type of the child node based on the correlation
        type of the parent and the Hadamard transition.
        - Create a new correlation node for the child and the correlation edge
        between the parent and the child.
        - Recursively call this method to find the correlation subgraphs starting
        from the child. Then add the edge in the last step to each of the subgraphs.
        Append the subgraphs to the `branched_subgraph`.
    3. Post-processing
        - If no subgraphs are found, return a single empty subgraph.
        - If the color of the node matches the correlation type, all the children
        should be traversed. Iterate through all the combinations where exactly one
        subgraph is selected from each child, and union them to form a new subgraph.
        Append the new subgraph to the `correlation_subgraphs`.
        - If the color of the node does not match the correlation type, only one
        child can be traversed. Append all the subgraphs in the `branched_subgraph`
        to the `correlation_subgraphs`.
    """
    correlation_subgraphs: list[set[ZXEdge]] = []
    parent_position = parent_corr_node.position
    parent_corr_type = parent_corr_node.node_type
    visited_positions.add(parent_position)

    branched_subgraphs: list[list[set[ZXEdge]]] = []
    for edge in zx_graph.edges_at(parent_position):
        cur_zx_node = edge.u if edge.v.position == parent_position else edge.v
        if cur_zx_node.position in visited_positions:
            continue
        cur_corr_type = (
            parent_corr_type.dual() if edge.has_hadamard else parent_corr_type
        )
        cur_corr_node = ZXNode(cur_zx_node.position, cur_corr_type)
        edge_between_cur_parent = ZXEdge(
            parent_corr_node, cur_corr_node, edge.has_hadamard
        )
        branched_subgraphs.append(
            [
                subgraph | {edge_between_cur_parent}
                for subgraph in _find_correlation_subgraphs_dfs(
                    zx_graph,
                    cur_corr_node,
                    cur_zx_node.node_type,
                    copy(visited_positions),
                )
            ]
        )
    if not branched_subgraphs:
        return [set()]
    # the color of node matches the correlation type
    # broadcast the correlation type to all the neighbors
    if parent_zx_node_type == parent_corr_type:
        for prod in itertools.product(*branched_subgraphs):
            correlation_subgraphs.append(set(itertools.chain(*prod)))
        return correlation_subgraphs

    # the color of node does not match the correlation type
    # only one of the neighbors can be the correlation path
    correlation_subgraphs.extend(itertools.chain(*branched_subgraphs))
    return correlation_subgraphs


def find_correlation_subgraphs(self) -> list[ZXGraph]:
    """Find the correlation subgraphs of the ZX graph.

    Here a correlation subgraph is defined as a subgraph of the `ZXGraph`
    that represents the correlation surface within a 3D spacetime diagram.
    Each node in the correlation subgraph is composed of its position and
    the correlation surface type, which is either `NodeType.X` or `NodeType.Z`.

    For the closed diagram, the correlation subgraph represents the correlation
    between the measured logical observables. For the open diagram, the
    correlation subgraph represents the correlation between the measured logical
    observables and the input/output observables, which can be combined with
    the expected stabilizer flow to verify the correctness of the computation.

    A recursive depth-first search algorithm is used to find the correlation
    subgraphs starting from each leaf node. The algorithm is described in the
    method `_find_correlation_subgraphs_dfs`.
    """
    single_node_correlation_subgraphs: list[ZXGraph] = []
    multi_edges_correlation_subgraphs: dict[frozenset[ZXEdge], ZXGraph] = {}
    num_subgraphs = 0
    for node in self.isolated_nodes:
        if node.is_port:
            continue
        subgraph = ZXGraph(f"Correlation subgraph {num_subgraphs}")
        subgraph.add_node(node.position, node.node_type)
        single_node_correlation_subgraphs.append(subgraph)
        num_subgraphs += 1

    def add_subgraphs(node: ZXNode, correlation_type: NodeType) -> None:
        nonlocal num_subgraphs
        root_corr_node = ZXNode(node.position, correlation_type)
        for edges in self._find_correlation_subgraphs_dfs(
            root_corr_node, node.node_type, set()
        ):
            if frozenset(edges) in multi_edges_correlation_subgraphs:
                continue
            subgraph = ZXGraph(f"Correlation subgraph {num_subgraphs} of {self.name}")
            for edge in edges:
                subgraph.add_edge(edge.u, edge.v, edge.has_hadamard)
            multi_edges_correlation_subgraphs[frozenset(edges)] = subgraph
            num_subgraphs += 1

    for node in self.leaf_nodes:
        if node.is_port:
            for correlation_type in [NodeType.X, NodeType.Z]:
                add_subgraphs(node, correlation_type)
        else:
            add_subgraphs(node, node.node_type)
    return single_node_correlation_subgraphs + list(
        multi_edges_correlation_subgraphs.values()
    )
