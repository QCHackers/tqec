"""Graph representation of a 3D spacetime defect diagram by explicit blocks."""

from __future__ import annotations

import pathlib
from typing import cast, TYPE_CHECKING
from copy import deepcopy
from io import BytesIO

import networkx as nx

from tqec.exceptions import TQECException
from tqec.position import Direction3D, Position3D
from tqec.computation.block_graph.cube import Cube, CubeKind, Port, ZXBasis, ZXCube
from tqec.computation.block_graph.pipe import Pipe, PipeKind
from tqec.computation.block_graph.observable import AbstractObservable
from tqec.computation.zx_graph import ZXKind, ZXGraph, ZXNode

if TYPE_CHECKING:
    from tqec.computation.collada import ColladaDisplayHelper


_CUBE_DATA_KEY = "tqec_block_cube_data"
_PIPE_DATA_KEY = "tqec_block_pipe_data"

BlockKind = CubeKind | PipeKind
"""Valid block types in the library."""


class BlockGraph:
    def __init__(self, name: str) -> None:
        """An undirected graph representation of a 3D spacetime defect diagram
        with the block structures explicitly defined."""
        self._name = name
        self._graph = nx.Graph()
        self._ports: dict[str, Position3D] = {}

    @property
    def name(self) -> str:
        """The name of the graph."""
        return self._name

    @property
    def num_ports(self) -> int:
        """The number of open ports in the graph."""
        return len(self._ports)

    @property
    def num_cubes(self) -> int:
        """The number of cubes in the graph"""
        return cast(int, self._graph.number_of_nodes())

    @property
    def num_pipes(self) -> int:
        """The number of pipes in the graph."""
        return cast(int, self._graph.number_of_edges())

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
        kind: CubeKind,
        label: str | None = None,
        check_conflict: bool = True,
    ) -> None:
        """Add a cube to the graph. If a cube already exists at the position, the
        cube kind will be updated.

        Args:
            position: The 3D position of the cube.
            kind: The kind of the cube.
            label: The label of the cube, if the cube is a port.
            check_conflict: Whether to check for cube conflict.

        Raises:
            TQECException: If a different cube already exists at the position.
            TQECException: If the port label is already used.
        """
        cube = Cube(position, kind, label)
        if check_conflict:
            self._check_cube_conflict(cube)
        self._graph.add_node(position, **{_CUBE_DATA_KEY: cube})
        if cube.is_port:
            assert cube.label is not None, "A port cube is guaranteed to have a label."
            self._ports[cube.label] = position

    def _check_cube_conflict(self, cube: Cube) -> None:
        """Check whether a new cube can be added to the graph without conflict."""
        position = cube.position
        if position in self:
            if self[position] == cube:
                return
            raise TQECException(
                f"The graph already has a different cube {self[position]} at this position."
            )
        if cube.is_port and cube.label in self._ports:
            raise TQECException(
                f"There is already a different port with label {cube.label} in the graph."
            )

    def add_pipe(self, u: Cube, v: Cube, kind: PipeKind) -> None:
        """Add a pipe to the graph. If the cubes do not exist in the graph,
        the cubes will be created.

        Args:
            u: The first cube of the edge.
            v: The second cube of the edge.
            pipe_type: The kind of the pipe

        """
        pipe = Pipe(u, v, kind)
        # Check before adding the cubes to avoid rolling back the changes
        self._check_cube_conflict(u)
        self._check_cube_conflict(v)
        self.add_cube(u.position, u.kind, u.label, check_conflict=False)
        self.add_cube(v.position, v.kind, v.label, check_conflict=False)
        self._graph.add_edge(u.position, v.position, **{_PIPE_DATA_KEY: pipe})

    def has_pipe_between(self, pos1: Position3D, pos2: Position3D) -> bool:
        """Check if there is an pipe between two positions."""
        return self._graph.has_edge(pos1, pos2)

    def pipes_at(self, position: Position3D) -> list[Pipe]:
        """Get the pipes connected to a cube."""
        return [
            data[_PIPE_DATA_KEY]
            for _, _, data in self._graph.edges(position, data=True)
        ]

    def get_pipe(self, pos1: Position3D, pos2: Position3D) -> Pipe:
        """Get the pipe by its endpoint positions.

        Args:
            pos1: The first endpoint position.
            pos2: The second endpoint position.

        Returns:
            The pipe between the two positions.

        Raises:
            TQECException: If there is no pipe between the given positions.
        """
        if not self.has_pipe_between(pos1, pos2):
            raise TQECException("No edge between the given positions in the graph.")
        return cast(Pipe, self._graph.edges[pos1, pos2][_PIPE_DATA_KEY])

    def __contains__(self, position: Position3D) -> bool:
        return position in self._graph

    def __getitem__(self, position: Position3D) -> ZXNode:
        return cast(ZXNode, self._graph.nodes[position][_CUBE_DATA_KEY])

    def validate(self) -> None:
        """Check the validity of the block structures represented by the graph.

        Refer to the Fig.9 in arXiv:2404.18369. Currently, we ignore the b) and e),
        only check the following conditions:
        a). no fanout: ports can only have one pipe connected to them.
        c). time-like Y: Y cubes can only have time-like pipes connected to them.
        d). no 3D corner: a cube cannot have pipes in all three directions.
        f). match color at passthrough: two pipes in a "pass-through" should have the same
        color orientation.
        g). match color at turn: two pipes in a "turn" should have the matching colors on
        faces that are touching.

        Args:
            allow_virtual_node: Whether to allow the virtual node in the graph. A virtual node is an open
                port of a pipe. It is not a physical cube but a placeholder for the pipe to connect to the
                boundary of the graph. Default is True.
        """
        for cube in self.cubes:
            self._validate_locally_at_cube(cube)

    def _validate_locally_at_cube(self, cube: Cube) -> None:
        """Check the validity of the block structures locally at a cube."""
        pipes = self.pipes_at(cube.position)
        # a). no fanout
        if cube.is_port:
            if len(pipes) != 1:
                raise TQECException(
                    f"Port at {cube.position} does not have exactly one pipe connected."
                )
            return
        # c). time-like Y
        if cube.is_y_cube:
            if not pipes:
                raise TQECException(f"Y cube at {cube.position} has no pipe connected.")
            if not all(pipe.direction == Direction3D.Z for pipe in pipes):
                raise TQECException(
                    f"Y cube at {cube.position} has non-time-like pipes connected."
                )
            return

        # Check the color matching conditions
        pipes_by_direction: dict[Direction3D, list[Pipe]] = {}
        for pipe in pipes:
            pipes_by_direction.setdefault(pipe.direction, []).append(pipe)
        pipe_directions = set(pipes_by_direction.keys())
        # d). No 3D corner
        if len(pipe_directions) == 3:
            raise TQECException(f"Cube at {cube.position} has a 3D corner pipes.")
        # f). Match color at passthrough
        for pipes in pipes:
            pipe.validate()
        # g). Match color at turn
        if len(pipe_directions) == 2:
            assert isinstance(cube.kind, ZXCube)
            # the surrounding walls perpendicular to the turn plane have the same color
            if cube.kind.normal_direction in pipe_directions:
                raise TQECException(
                    f"Pipes turn at {cube.position} do not have matching colors."
                )

    def to_zx_graph(self, name: str | None = None) -> ZXGraph:
        """Convert the block graph to a ZX graph."""
        zx_graph = ZXGraph(name or self.name)
        for cube in self.cubes:
            node = cube.to_zx_node()
            zx_graph.add_node(node.position, node.kind, node.label)
        for pipe in self.pipes:
            zx_graph.add_edge(
                pipe.u.to_zx_node(), pipe.v.to_zx_node(), pipe.kind.has_hadamard
            )
        return zx_graph

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BlockGraph):
            return False
        return cast(bool, nx.utils.graphs_equal(self._graph, other._graph))

    @staticmethod
    def from_zx_graph(zx_graph: ZXGraph, name: str | None = None) -> BlockGraph:
        """Construct a block graph from a ZX graph.

        The ZX graph includes the minimal information required to construct the block graph,
        but not guaranteed to admit a valid block structure. The block structure will be inferred
        from the ZX graph and validated.

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
        # The color of corner cubes can be inferred locally from the ZX graph
        corner_cubes: set[Cube] = set()
        for node in set(nodes_to_handle):
            directions = {e.direction for e in zx_graph.edges_at(node.position)}
            if len(directions) != 2:
                continue
            normal_direction = (
                set(Direction3D.all_directions()).difference(directions).pop()
            )
            kind = ZXCube.from_normal_basis(ZXBasis(node.kind.value), normal_direction)
            block_graph.add_cube(node.position, kind, node.label)
            nodes_to_handle.remove(node)
            corner_cubes.add(Cube(node.position, kind, node.label))

        # BFS traverse starting from a known-kind node to infer the kinds of others
        bfs_source = next((c.position for c in corner_cubes), None)
        # If no corner cube can be found, then specify the kind of a ZX node with
        # minimum position in the graph
        if bfs_source is None:
            nodes_sorted_by_pos: list[ZXNode] = sorted(
                nodes_to_handle, key=lambda n: n.position
            )
            specified_node = next(
                n for n in nodes_sorted_by_pos if not n.is_port and not n.is_y_node
            )
            edges_at_node = zx_graph.edges_at(specified_node.position)
            # Special case: single node ZXGraph
            if len(edges_at_node) == 1:
                specified_kind = (
                    ZXCube.from_str("ZXZ")
                    if specified_node.kind == ZXKind.X
                    else ZXCube.from_str("ZXX")
                )
            else:
                # the basis along the edge direction must be the opposite of the node kind
                basis = ["X", "Z"]
                basis.insert(
                    edges_at_node[0].direction.value,
                    specified_node.kind.with_zx_flipped().value,
                )
                specified_kind = ZXCube.from_str("".join(basis))
            bfs_source = specified_node.position
            block_graph.add_cube(bfs_source, specified_kind, specified_node.label)
            nodes_to_handle.remove(specified_node)

        for p1, p2 in nx.bfs_edges(zx_graph.nx_graph, bfs_source):
            edge = zx_graph.get_edge(p1, p2)
            if edge not in edges_to_handle:
                continue
            src_node, dst_node = edge.u, edge.v
            # Special case for port connects to y node: select pipe arbitrarily and consistently
            if {src_node.kind, dst_node.kind} == {ZXKind.P, ZXKind.Y}:
                bases: list[ZXBasis | None] = [ZXBasis.X, ZXBasis.Z]
                bases.insert(edge.direction.value, None)
                pipe_type = PipeKind(*bases, has_hadamard=edge.has_hadamard)
                continue
            # There must be at least one handled cube in the edge due to the BFS traversal
            handled_index = 1 if src_node in nodes_to_handle else 0
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

        block_graph.validate()
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

    def get_abstract_observables(
        self,
    ) -> tuple[list[AbstractObservable], list[ZXGraph]]:
        """Get all the abstract observables from the block graph."""
        self.check_validity(allow_virtual_node=False)
        correlation_subgraphs = self.to_zx_graph().find_correlation_subgraphs()
        abstract_observables: list[AbstractObservable] = []

        def is_measured(cube: Cube) -> bool:
            return self.get_pipe(cube.position, cube.position.shift_by(0, 0, 1)) is None

        for g in correlation_subgraphs:
            if g.num_nodes == 1:
                cube = self.get_cube(g.nodes[0].pos)
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
                pipe = self.get_pipe(edge.u.pos, edge.v.pos)
                assert (
                    pipe is not None
                ), f"{edge} is in the graph and should be associated with a Pipe instance."
                u, v = pipe.u, pipe.v
                if pipe.direction == Direction3D.Z:
                    if is_measured(v) and v.kind.value[2] == correlation_type_at_dst:
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
        return abstract_observables, correlation_subgraphs

    def with_zero_min_z(self) -> BlockGraph:
        """Shift the whole graph in the z direction to make the minimum z
        zero."""
        minz = min(cube.position.z for cube in self.cubes)
        if minz == 0:
            return deepcopy(self)
        new_graph = BlockGraph(self.name)
        for cube in self.cubes:
            new_graph.add_cube(cube.position.shift_by(dz=-minz), cube.kind)
        for pipe in self.pipes:
            new_graph.add_pipe(
                pipe.u.position.shift_by(dz=-minz),
                pipe.v.position.shift_by(dz=-minz),
                pipe.pipe_type,
            )
        return new_graph
