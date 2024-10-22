"""Conversion between `ZXGraph` and `BlockGraph`."""

from typing import cast
from tqec.computation.cube import (
    Cube,
    CubeKind,
    Port,
    YCube,
    ZXBasis,
    ZXCube,
)
from tqec.computation.block_graph import BlockGraph
from tqec.computation.pipe import PipeKind
from tqec.computation.zx_graph import ZXEdge, ZXGraph, ZXKind, ZXNode
from tqec.exceptions import TQECException
from tqec.position import Direction3D


def convert_block_graph_to_zx_graph(
    block_graph: BlockGraph, name: str | None = None
) -> ZXGraph:
    """Convert the block graph to a ZX graph."""
    zx_graph = ZXGraph(name or block_graph.name)
    for cube in block_graph.cubes:
        node = cube.to_zx_node()
        zx_graph.add_node(node.position, node.kind, node.label)
    for pipe in block_graph.pipes:
        zx_graph.add_edge(
            pipe.u.to_zx_node(), pipe.v.to_zx_node(), pipe.kind.has_hadamard
        )
    return zx_graph


def convert_zx_graph_to_block_graph(
    zx_graph: ZXGraph, name: str | None = None
) -> BlockGraph:
    """Convert the ZX graph to a block graph.

    The ZX graph includes the minimal information required to construct the block graph,
    but not guaranteed to admit a valid block structure. The block structure will be inferred
    from the ZX graph and validated.

    The conversion process is as follows:
    1. Construct cubes for all the corner nodes in the ZX graph.
    2. Construct pipes connecting ports/Y to ports/Y nodes.
    3. Greedily construct the pipes until no more pipes can be inferred.
    4. If there are still nodes left, then choose orientation for an arbitrary node
    and repeat 3. Repeat 4 until all nodes are handled or conflicts are detected.

    Args:
        zx_graph: The base ZX graph to construct the block graph.
        name: The name of the new block graph. If None, the name of the ZX graph will be used.

    Returns:
        The constructed block graph.
    """
    # validate the ZX graph before constructing the block graph
    zx_graph.validate()

    nodes_to_handle = set(zx_graph.nodes)
    edges_to_handle = set(zx_graph.edges)

    block_graph = BlockGraph(name or zx_graph.name)
    # 1. Construct cubes for all the corner nodes in the ZX graph.
    _handle_corners(zx_graph, block_graph, nodes_to_handle)

    # 2. Construct pipes connecting ports/Y to ports/Y nodes.
    _handle_special_pipes(block_graph, nodes_to_handle, edges_to_handle)

    # 3. Greedily construct the pipes until no more pipes can be inferred.
    _greedily_construct_blocks(block_graph, nodes_to_handle, edges_to_handle)

    # 4. If there are still nodes left, then choose orientation for an arbitrary node
    # and repeat 3. Repeat 4 until all nodes are handled or conflicts are detected.
    _handle_leftover_nodes(zx_graph, block_graph, nodes_to_handle, edges_to_handle)

    block_graph.validate()
    return block_graph


def _handle_corners(
    zx_graph: ZXGraph, block_graph: BlockGraph, nodes_to_handle: set[ZXNode]
) -> None:
    for node in zx_graph.nodes:
        directions = {e.direction for e in zx_graph.edges_at(node.position)}
        if len(directions) != 2:
            continue
        normal_direction = (
            set(Direction3D.all_directions()).difference(directions).pop()
        )
        kind = ZXCube.from_normal_basis(ZXBasis(node.kind.value), normal_direction)
        block_graph.add_cube(node.position, kind, node.label)
        nodes_to_handle.remove(node)


def _handle_special_pipes(
    block_graph: BlockGraph,
    nodes_to_handle: set[ZXNode],
    edges_to_handle: set[ZXEdge],
) -> None:
    for edge in edges_to_handle:
        u, v = edge.u, edge.v
        if u.is_zx_node or v.is_zx_node:
            continue
        pipe_kind = _choose_arbitrary_pipe_kind(edge)
        block_graph.add_pipe(
            Cube(u.position, Port() if u.is_port else YCube(), u.label),
            Cube(v.position, Port() if v.is_port else YCube(), v.label),
            pipe_kind,
        )
        nodes_to_handle.remove(u)
        nodes_to_handle.remove(v)
        edges_to_handle.remove(edge)


def _greedily_construct_blocks(
    block_graph: BlockGraph,
    nodes_to_handle: set[ZXNode],
    edges_to_handle: set[ZXEdge],
) -> None:
    num_nodes_left = len(nodes_to_handle) + 1
    while len(nodes_to_handle) < num_nodes_left:
        num_nodes_left = len(nodes_to_handle)
        _try_to_handle_edges(block_graph, nodes_to_handle, edges_to_handle)


def _try_to_handle_edges(
    block_graph: BlockGraph,
    nodes_to_handle: set[ZXNode],
    edges_to_handle: set[ZXEdge],
) -> None:
    for edge in set(edges_to_handle):
        u, v = edge.u, edge.v
        if u in nodes_to_handle and v in nodes_to_handle:
            continue
        can_infer_from_u = u not in nodes_to_handle and u.is_zx_node
        can_infer_from_v = v not in nodes_to_handle and v.is_zx_node
        if not can_infer_from_u and not can_infer_from_v:
            continue
        infer_from, other_node = (u, v) if can_infer_from_u else (v, u)
        cube_kind = cast(ZXCube, block_graph[infer_from.position].kind)
        pipe_kind = _infer_pipe_kind_from_endpoint(
            cube_kind, edge.direction, can_infer_from_u, edge.has_hadamard
        )
        other_cube_kind: CubeKind
        if other_node.is_zx_node:
            other_cube_kind = _infer_cube_kind_from_pipe(
                pipe_kind,
                not can_infer_from_u,
                v.kind if can_infer_from_u else u.kind,
            )
            # Check cube kind conflicts
            if other_node not in nodes_to_handle:
                existing_kind = block_graph[other_node.position].kind
                if not other_cube_kind == existing_kind:
                    raise TQECException(
                        f"Encounter conflicting cube kinds at {other_node.position}: "
                    )
        else:
            other_cube_kind = Port() if other_node.is_port else YCube()
        block_graph.add_pipe(
            block_graph[infer_from.position],
            Cube(other_node.position, other_cube_kind, other_node.label),
            pipe_kind,
        )
        if other_node in nodes_to_handle:
            nodes_to_handle.remove(other_node)
        edges_to_handle.remove(edge)


def _fix_kind_for_one_node(
    zx_graph: ZXGraph,
    block_graph: BlockGraph,
    nodes_to_handle: set[ZXNode],
) -> None:
    sorted_nodes = sorted(nodes_to_handle, key=lambda n: n.position)[0]
    fix_kind_node = next(n for n in sorted_nodes if n.is_zx_node)
    edges_at_node = zx_graph.edges_at(fix_kind_node.position)
    # Special case: single node ZXGraph
    if len(edges_at_node) == 1:
        specified_kind = (
            ZXCube.from_str("ZXZ")
            if fix_kind_node.kind == ZXKind.X
            else ZXCube.from_str("ZXX")
        )
    else:
        # the basis along the edge direction must be the opposite of the node kind
        basis = ["X", "Z"]
        basis.insert(
            edges_at_node[0].direction.value,
            fix_kind_node.kind.with_zx_flipped().value,
        )
        specified_kind = ZXCube.from_str("".join(basis))
    block_graph.add_cube(fix_kind_node.position, specified_kind, fix_kind_node.label)


def _handle_leftover_nodes(
    zx_graph: ZXGraph,
    block_graph: BlockGraph,
    nodes_to_handle: set[ZXNode],
    edges_to_handle: set[ZXEdge],
) -> None:
    while nodes_to_handle:
        _fix_kind_for_one_node(zx_graph, block_graph, nodes_to_handle)
        _greedily_construct_blocks(block_graph, nodes_to_handle, edges_to_handle)


def _choose_arbitrary_pipe_kind(edge: ZXEdge) -> PipeKind:
    bases: list[ZXBasis | None] = [ZXBasis.X, ZXBasis.Z]
    bases.insert(edge.direction.value, None)
    return PipeKind(*bases, has_hadamard=edge.has_hadamard)


def _infer_pipe_kind_from_endpoint(
    endpoint_kind: ZXCube,
    pipe_direction: Direction3D,
    at_pipe_head: bool,
    has_hadamard: bool = False,
) -> PipeKind:
    """Infer the pipe kind from the endpoint cube kind and the pipe direction."""
    bases: list[ZXBasis | None]
    if not at_pipe_head and has_hadamard:
        bases = [basis.with_zx_flipped() for basis in endpoint_kind.as_tuple()]
    else:
        bases = list(endpoint_kind.as_tuple())
    bases[pipe_direction.value] = None
    return PipeKind(*bases, has_hadamard=has_hadamard)


def _infer_cube_kind_from_pipe(
    pipe_kind: PipeKind,
    at_pipe_head: bool,
    node_kind: ZXKind,
) -> ZXCube:
    """Infer the cube kinds from the pipe kind."""
    bases = [
        pipe_kind.get_basis_along(direction, at_pipe_head)
        for direction in Direction3D.all_directions()
    ]
    bases[pipe_kind.direction.value] = ZXBasis(node_kind.value).with_zx_flipped()
    return ZXCube(*cast(list[ZXBasis], bases))
