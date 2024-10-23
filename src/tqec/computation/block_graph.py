"""Graph representation of a 3D spacetime defect diagram by explicit blocks."""

from __future__ import annotations

import pathlib
from typing import cast, TYPE_CHECKING
from copy import deepcopy
from io import BytesIO

import networkx as nx

from tqec.exceptions import TQECException
from tqec.position import Direction3D, Position3D
from tqec.computation.cube import Cube, CubeKind
from tqec.computation.pipe import Pipe, PipeKind
from tqec.computation.zx_graph import ZXGraph
from tqec.computation.correlation import CorrelationSurface

if TYPE_CHECKING:
    from tqec.computation.collada import ColladaDisplayHelper
    from tqec.computation.abstract_observable import AbstractObservable


_CUBE_DATA_KEY = "tqec_block_cube_data"
_PIPE_DATA_KEY = "tqec_block_pipe_data"

BlockKind = CubeKind | PipeKind
"""Valid block types in the library."""


class BlockGraph:
    def __init__(self, name: str = "") -> None:
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
    def ports(self) -> dict[str, Position3D]:
        """The open ports in the graph."""
        return self._ports

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

    def __getitem__(self, position: Position3D) -> Cube:
        return cast(Cube, self._graph.nodes[position][_CUBE_DATA_KEY])

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
            if len(pipes) != 1:
                raise TQECException(
                    f"Y cube at {cube.position} does not have exactly one pipe connected."
                )
            if not pipes[0].direction == Direction3D.Z:
                raise TQECException(
                    f"Y cube at {cube.position} has non-timelike pipes connected."
                )
            return

        # Check the color matching conditions
        pipes_by_direction: dict[Direction3D, list[Pipe]] = {}
        for pipe in pipes:
            pipes_by_direction.setdefault(pipe.direction, []).append(pipe)
        # d), f), g). Match color
        for pipes in pipes:
            pipe.validate()

    def to_zx_graph(self, name: str | None = None) -> ZXGraph:
        """Convert the block graph to a ZX graph."""
        from tqec.computation.conversion import (
            convert_block_graph_to_zx_graph,
        )

        return convert_block_graph_to_zx_graph(self, name)

    @staticmethod
    def from_zx_graph(zx_graph: ZXGraph, name: str | None = None) -> BlockGraph:
        """Construct the block graph from a ZX graph."""
        from tqec.computation.conversion import (
            convert_zx_graph_to_block_graph,
        )

        return convert_zx_graph_to_block_graph(zx_graph, name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BlockGraph):
            return False
        return cast(bool, nx.utils.graphs_equal(self._graph, other._graph))

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
        correlation_surfaces: list[CorrelationSurface] | None = None,
    ) -> tuple[list[AbstractObservable], list[CorrelationSurface]]:
        """Get all the abstract observables from the block graph."""
        from tqec.computation.abstract_observable import (
            correlation_surface_to_abstract_observable,
        )

        self.validate()
        # Edge case: only one cube in the graph
        if self.num_cubes == 1:
            return [AbstractObservable(frozenset(self.cubes), frozenset())], []

        if correlation_surfaces is None:
            correlation_surfaces = self.to_zx_graph().find_correration_surfaces()
        abstract_observables: list[AbstractObservable] = [
            correlation_surface_to_abstract_observable(self, surface)
            for surface in correlation_surfaces
        ]

        return abstract_observables, correlation_surfaces

    def shift_min_z_to_zero(self) -> BlockGraph:
        """Shift the whole graph in the z direction to make the minimum z equal zero."""
        minz = min(cube.position.z for cube in self.cubes)
        if minz == 0:
            return deepcopy(self)
        new_graph = BlockGraph(self.name)
        for pipe in self.pipes:
            u, v = pipe.u, pipe.v
            new_graph.add_pipe(
                Cube(u.position.shift_by(dz=-minz), u.kind, u.label),
                Cube(v.position.shift_by(dz=-minz), v.kind, v.label),
                pipe.kind,
            )
        return new_graph
