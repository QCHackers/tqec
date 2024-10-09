"""Graph representation of a 3D spacetime defect diagram by explicit blocks."""

from __future__ import annotations

import pathlib
import typing as ty
from copy import deepcopy
from io import BytesIO

import networkx as nx

from tqec.exceptions import TQECException
from tqec.position import Direction3D, Position3D
from tqec.computation.block_graph.cube import Cube
from tqec.computation.block_graph.enums import CubeType, PipeType
from tqec.computation.block_graph.observable import AbstractObservable
from tqec.computation.block_graph.pipe import Pipe
from tqec.computation.zx_graph import NodeType, ZXGraph, ZXNode

if ty.TYPE_CHECKING:
    from tqec.computation.collada import ColladaDisplayHelper


_CUBE_DATA_KEY = "tqec_block_cube_data"
_PIPE_DATA_KEY = "tqec_block_pipe_data"


class BlockGraph:
    def __init__(self, name: str) -> None:
        """An undirected graph representation of a 3D spacetime defect diagram
        with the block structures explicitly defined."""
        self._name = name
        self._graph = nx.Graph()

    @property
    def name(self) -> str:
        """The name of the graph."""
        return self._name

    @property
    def num_cubes(self) -> int:
        """The number of cubes in the graph."""
        return ty.cast(int, self._graph.number_of_nodes())

    @property
    def num_pipes(self) -> int:
        """The number of pipes in the graph."""
        return ty.cast(int, self._graph.number_of_edges())

    @property
    def num_open_ports(self) -> int:
        """The number of open ports in the graph."""
        return sum(cube.is_virtual for cube in self.cubes)

    @property
    def cubes(self) -> list[Cube]:
        """Return a list of cubes in the graph."""
        return [data[_CUBE_DATA_KEY] for _, data in self._graph.nodes(data=True)]

    @property
    def pipes(self) -> list[Pipe]:
        """Return a list of pipes in the graph."""
        return [data[_PIPE_DATA_KEY] for _, _, data in self._graph.edges(data=True)]

    def add_cube(
        self,
        position: Position3D,
        cube_type: CubeType,
    ) -> None:
        """Add a cube to the graph.

        Args:
            position: The 3D position of the node.
            cube_type: The type of the cube.
        """
        if position in self._graph:
            raise TQECException(f"Cube at {position} already exists in the graph.")
        self._graph.add_node(position, **{_CUBE_DATA_KEY: Cube(position, cube_type)})

    def add_pipe(self, u: Position3D, v: Position3D, pipe_type: PipeType) -> None:
        """Add a pipe to the graph.

        Args:
            u: The position of the first cube.
            v: The position of the second cube.
            pipe_type: The type of the pipe.
        """
        if u not in self._graph or v not in self._graph:
            raise TQECException("Both cubes must exist in the graph.")
        u_node = self._graph.nodes[u][_CUBE_DATA_KEY]
        v_node = self._graph.nodes[v][_CUBE_DATA_KEY]
        self._graph.add_edge(u, v, **{_PIPE_DATA_KEY: Pipe(u_node, v_node, pipe_type)})

    def get_cube(self, position: Position3D) -> Cube | None:
        """Get the cube by position."""
        if position not in self._graph:
            return None
        return ty.cast(Cube, self._graph.nodes[position][_CUBE_DATA_KEY])

    def get_pipe(self, u: Position3D, v: Position3D) -> Pipe | None:
        """Get the pipe by its endpoint cube positions."""
        if not self._graph.has_edge(u, v):
            return None
        return ty.cast(Pipe, self._graph.edges[u, v][_PIPE_DATA_KEY])

    def pipes_at(self, position: Position3D) -> list[Pipe]:
        """Get the pipes connected to a cube."""
        return [
            data[_PIPE_DATA_KEY]
            for _, _, data in self._graph.edges(position, data=True)
        ]

    def check_validity(self, allow_virtual_node: bool = True) -> None:
        """Check the validity of the block structures represented by the graph.

        Refer to the Fig.9 in arXiv:2404.18369. Currently, we only check the constraints
        d, f and g in the figure:

        1. No 3D corner: all the pipes are within the same plane.
        2. Match color at pass-through: the pipes and cube have the same color at the
            pass-through.
        3. Match color at turn: the pipes and cube have the same color at the bent side
            of the turn.

        Args:
            allow_virtual_node: Whether to allow the virtual node in the graph. A virtual node is an open
                port of a pipe. It is not a physical cube but a placeholder for the pipe to connect to the
                boundary of the graph. Default is True.
        """
        if not allow_virtual_node and any(cube.is_virtual for cube in self.cubes):
            raise TQECException("The graph contains a virtual node.")
        for cube in self.cubes:
            self._check_validity_locally_at_cube(cube)

    def _check_validity_locally_at_cube(self, cube: Cube) -> None:
        """Check the validity of the block structures locally at a cube."""
        # Skip the virtual cube
        if cube.is_virtual:
            return
        pipes_by_direction: dict[Direction3D, list[Pipe]] = {}
        for pipe in self.pipes_at(cube.position):
            pipes_by_direction.setdefault(pipe.pipe_type.direction, []).append(pipe)
        pipe_directions = set(pipes_by_direction.keys())
        # 1. No 3D corner
        if len(pipe_directions) == 3:
            raise TQECException(f"Cube at {cube.position} has a 3D corner.")
        # 2. Match color at pass-through
        cube_color = cube.cube_type.get_color()
        for direction, pipes in pipes_by_direction.items():
            if not all(
                pipe.pipe_type.get_color_at_side(pipe.u == cube).match(cube_color)
                for pipe in pipes
            ):
                raise TQECException(
                    f"Cube at {cube.position} has unmatched color at pass-through along {direction} direction."
                )
        # 3. Match color at turn
        if len(pipe_directions) == 2:
            # since we have checked the pass-through match
            # we only have to check that the surrounding walls at the turn plane have the same color
            if cube.cube_type.normal_direction_to_corner_plane() in pipe_directions:
                raise TQECException(
                    f"Cube at {cube.position} has unmatched color at turn."
                )

    def __contains__(self, position: Position3D) -> bool:
        """Check if there is a cube at the position."""
        return position in self._graph

    def to_zx_graph(self, name: str = "") -> ZXGraph:
        """Convert the block graph to a ZX graph."""
        zx_graph = ZXGraph(name if name else self.name + "_zx")
        for cube in self.cubes:
            zx_graph.add_node(cube.position, cube.cube_type.to_zx_node_type())
        for pipe in self.pipes:
            zx_graph.add_edge(
                pipe.u.position, pipe.v.position, pipe.pipe_type.has_hadamard
            )
        return zx_graph

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BlockGraph):
            return False
        return ty.cast(bool, nx.utils.graphs_equal(self._graph, other._graph))

    @staticmethod
    def from_zx_graph(zx_graph: ZXGraph, name: str = "") -> BlockGraph:
        """Construct a block graph from a ZX graph.

        The ZX graph includes the minimal information required to construct the block graph,
        but not guaranteed to admit a valid block structure. The block structure will be inferred
        from the ZX graph and validated.

        Args:
            zx_graph: The base ZX graph to construct the block graph.
            name: The name of the new block graph.

        Returns:
            The constructed block graph.
        """
        block_graph = BlockGraph(name if name else zx_graph.name + "_block")

        nodes_to_handle = set(zx_graph.nodes)
        edges_to_handle = set(zx_graph.edges)

        # Add the virtual nodes first
        for node in zx_graph.nodes:
            if node.is_virtual:
                block_graph.add_cube(node.position, CubeType.VIRTUAL)
                nodes_to_handle.remove(node)
        # Check 3D corner
        for node in nodes_to_handle:
            if len({e.direction for e in zx_graph.edges_at(node.position)}) == 3:
                raise TQECException(f"ZX graph has a 3D corner at {node.position}.")
        # The color of corner cubes can be inferred locally from the ZX graph
        # by querying which plane the corner is in and the color of the ZX node.
        corner_cubes: dict[Position3D, Cube] = {}
        for node in set(nodes_to_handle):
            edge_directions_at_node = {
                e.direction for e in zx_graph.edges_at(node.position)
            }
            if len(edge_directions_at_node) != 2:
                continue
            node_type = node.node_type
            normal_direction = (
                set(Direction3D.all()).difference(edge_directions_at_node).pop()
            )
            direction_index = Direction3D.all().index(normal_direction)
            normal_direction_color = "x" if node_type == NodeType.Z else "z"
            cube_type_str = str(node_type.value) * 3
            cube_type_str = (
                cube_type_str[:direction_index]
                + normal_direction_color
                + cube_type_str[direction_index + 1 :]
            )
            cube_type = CubeType(cube_type_str)
            block_graph.add_cube(node.position, cube_type)
            nodes_to_handle.remove(node)
            corner_cubes[node.position] = Cube(node.position, cube_type)

        # Infer the block structure from the corner cubes
        # BFS traverse each connected component from a corner node in that component
        bfs_sources: list[Cube] = []
        for component in nx.connected_components(zx_graph.nx_graph):
            # find one corner node in the component
            corner_cube_in_component = None
            for pos in component:
                if pos in corner_cubes:
                    corner_cube_in_component = corner_cubes[pos]
                    bfs_sources.append(corner_cube_in_component)
                    break
            # No corner cube can be found, then choose the orientation
            # of a non-virtual node with minimum position in the component
            if corner_cube_in_component is None:
                sorted_positions: list[Position3D] = sorted(component)
                aligned_node = next(
                    ty.cast(ZXNode, zx_graph.get_node(pos))
                    for pos in sorted_positions
                    if not ty.cast(ZXNode, zx_graph.get_node(pos)).is_virtual
                )
                node_pos, node_type = aligned_node.position, aligned_node.node_type
                edges_at_node = zx_graph.edges_at(node_pos)
                if not edges_at_node:
                    aligned_node_type = (
                        CubeType.XZZ if node_type == NodeType.Z else CubeType.XZX
                    )
                else:
                    edge_direction = edges_at_node[0].direction
                    node_type_list = ["x", "z"]
                    node_type_list.insert(
                        edge_direction.axis_index,
                        "x" if node_type == NodeType.X else "z",
                    )
                    aligned_node_type = CubeType("".join(node_type_list))
                block_graph.add_cube(aligned_node.position, aligned_node_type)
                nodes_to_handle.remove(aligned_node)
                bfs_sources.append(Cube(aligned_node.position, aligned_node_type))
        for src_cube in bfs_sources:
            for p1, p2 in nx.bfs_edges(zx_graph.nx_graph, src_cube.position):
                edge = zx_graph.get_edge(p1, p2)
                assert (
                    edge is not None
                ), "Post-condition of `get_edge` broken, a supposedly existing edge returned None"
                if edge not in edges_to_handle:
                    continue
                p1, p2 = sorted((p1, p2))
                src = ty.cast(ZXNode, zx_graph.get_node(p1))
                dst = ty.cast(ZXNode, zx_graph.get_node(p2))
                can_infer_from_src = src not in nodes_to_handle and not src.is_virtual
                can_infer_from_dst = dst not in nodes_to_handle and not dst.is_virtual
                if not can_infer_from_src and not can_infer_from_dst:
                    raise TQECException(
                        f"Cannot infer the pipe structure from the ZX graph at edge {p1} -> {p2}."
                    )

                known_cube = ty.cast(
                    Cube, block_graph.get_cube(p1 if can_infer_from_src else p2)
                )
                pipe_type = known_cube.cube_type.infer_pipe_type_at_direction(
                    edge.direction, can_infer_from_src, edge.has_hadamard
                )
                if src in nodes_to_handle or dst in nodes_to_handle:
                    other_node = dst if can_infer_from_src else src
                    other_cube_type = pipe_type.infer_cube_type_at_side(
                        not can_infer_from_src, other_node.node_type == NodeType.Z
                    )
                    block_graph.add_cube(other_node.position, other_cube_type)
                    nodes_to_handle.remove(other_node)
                block_graph.add_pipe(p1, p2, pipe_type)
                edges_to_handle.remove(edge)

        if nodes_to_handle:
            raise TQECException(
                f"The cube structure at positions {[n.position for n in nodes_to_handle]} cannot be resolved."
            )
        if edges_to_handle:
            raise TQECException(
                f"The pipe structure at {[(e.u.position, e.v.position) for e in edges_to_handle]} cannot be resolved."
            )

        block_graph.check_validity(allow_virtual_node=True)
        return block_graph

    def to_dae_file(
        self, filename: str | pathlib.Path, pipe_length: float = 2.0
    ) -> None:
        """Export the block graph to a DAE file."""
        from tqec.computation.collada import write_block_graph_to_dae_file

        write_block_graph_to_dae_file(self, filename, pipe_length)

    @staticmethod
    def from_dae_file(filename: str | pathlib.Path, graph_name: str = "") -> BlockGraph:
        """Construct a block graph from a DAE file."""
        from tqec.computation.collada import read_block_graph_from_dae_file

        return read_block_graph_from_dae_file(filename, graph_name)

    def display(
        self,
        write_html_filepath: str | pathlib.Path | None = None,
        pipe_length: float = 2.0,
    ) -> ColladaDisplayHelper:
        """Display the block graph in 3D."""
        from tqec.computation.collada import (
            display_collada_model,
            write_block_graph_to_dae_file,
        )

        bytes_buffer = BytesIO()
        write_block_graph_to_dae_file(self, bytes_buffer, pipe_length)
        return display_collada_model(
            filepath_or_bytes=bytes_buffer.getvalue(),
            write_html_filepath=write_html_filepath,
        )

    def get_abstract_observables(self) -> list[AbstractObservable]:
        """Get all the abstract observables from the block graph."""
        self.check_validity(allow_virtual_node=False)
        correlation_subgraphs = self.to_zx_graph().find_correlation_subgraphs()
        abstract_observables: list[AbstractObservable] = []

        def is_measured(cube: Cube) -> bool:
            return self.get_pipe(cube.position, cube.position.shift_by(0, 0, 1)) is None

        for g in correlation_subgraphs:
            if g.num_nodes == 1:
                cube = self.get_cube(g.nodes[0].position)
                assert (
                    cube is not None
                ), f"{g.nodes[0]} is in the graph and should be associated with a Cube instance."
                abstract_observables.append(
                    AbstractObservable(frozenset({cube}), frozenset())
                )
                continue
            top_lines: set[Cube | Pipe] = set()
            bottom_regions: set[Pipe] = set()
            for edge in g.edges:
                correlation_type_at_src = edge.u.node_type.value
                correlation_type_at_dst = edge.v.node_type.value
                pipe = self.get_pipe(edge.u.position, edge.v.position)
                assert (
                    pipe is not None
                ), f"{edge} is in the graph and should be associated with a Pipe instance."
                u, v = pipe.u, pipe.v
                if pipe.direction == Direction3D.Z:
                    if (
                        is_measured(v)
                        and v.cube_type.value[2] == correlation_type_at_dst
                    ):
                        top_lines.add(v)
                    continue
                # The direction for which the correlation surface of that type
                # can be attached to the pipe
                correlation_type_direction = Direction3D.from_axis_index(
                    pipe.pipe_type.value.index(correlation_type_at_src)
                )
                if correlation_type_direction == Direction3D.Z:
                    top_lines.add(pipe)
                    if is_measured(u):
                        top_lines.add(u)
                    if is_measured(v):
                        top_lines.add(v)
                else:
                    bottom_regions.add(pipe)
            abstract_observables.append(
                AbstractObservable(frozenset(top_lines), frozenset(bottom_regions))
            )
        return abstract_observables

    def with_zero_min_z(self) -> BlockGraph:
        """Shift the whole graph in the z direction to make the minimum z
        zero."""
        minz = min(cube.position.z for cube in self.cubes)
        if minz == 0:
            return deepcopy(self)
        new_graph = BlockGraph(self.name)
        for cube in self.cubes:
            new_graph.add_cube(cube.position.shift_by(dz=-minz), cube.cube_type)
        for pipe in self.pipes:
            new_graph.add_pipe(
                pipe.u.position.shift_by(dz=-minz),
                pipe.v.position.shift_by(dz=-minz),
                pipe.pipe_type,
            )
        return new_graph
