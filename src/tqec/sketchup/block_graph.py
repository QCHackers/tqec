"""Graph representation of a 3D spacetime defect diagram by explicit blocks."""
from __future__ import annotations

import typing as ty
from dataclasses import dataclass, astuple
from enum import Enum, auto

import networkx as nx

from tqec.sketchup.zx_graph import Position3D, ZXGraph, NodeType
from tqec.exceptions import TQECException


@dataclass(frozen=True)
class Color3D:
    """Get face colors along the x, y, and z axes."""
    x: str | None
    y: str | None
    z: str | None

    def match(self, other: Color3D) -> bool:
        """Check whether the color matches the other color."""
        return all(c1 is None or c2 is None or c1 == c2 for c1, c2 in zip(astuple(self), astuple(other)))

    @staticmethod
    def from_string(s: str, flip_xz: bool = False) -> "Color3D":
        s = s.lower()
        if s == "virtual":
            return Color3D(None, None, None)
        if len(s) != 3 or any(c not in "xzo" for c in s):
            raise TQECException("s must be a 3-character string containing only 'x', 'z', and 'o'.")
        colors: list[str | None] = []
        for c in s:
            if c == "o":
                colors.append(None)
            elif flip_xz:
                colors.append("z" if c == "x" else "x")
            else:
                colors.append(c)
        return Color3D(*colors)


class CubeType(Enum):
    """Valid cube types in the library."""
    ZXX = "zxx"
    XZX = "xzx"
    XXZ = "xxz"
    XZZ = "xzz"
    ZXZ = "zxz"
    ZZX = "zzx"
    # Virtual cube for open port
    VIRTUAL = "virtual"

    @property
    def is_virtual(self) -> bool:
        """Check if the block type is a virtual block."""
        return self == CubeType.VIRTUAL

    def to_zx_node_type(self) -> NodeType:
        """Convert the cube type to a ZX node type."""
        if self.is_virtual:
            return NodeType.V
        return NodeType.Z if self.value.count("z") == 2 else NodeType.X

    def get_color(self) -> Color3D:
        """Get the color of the block."""
        return Color3D.from_string(self.value)

    def normal_direction_to_corner_plane(self) -> Direction3D | None:
        """If the cube is at a corner, return the normal direction to the corner plane."""
        if self.is_virtual:
            return None
        if self.value.count("z") == 2:
            return Direction3D.from_axis_index(self.value.index("x"))
        return Direction3D.from_axis_index(self.value.index("z"))


class Direction3D(Enum):
    """Axis directions in the 3D spacetime diagram."""
    X = auto()
    Y = auto()
    Z = auto()

    @staticmethod
    def from_axis_index(i: int) -> Direction3D:
        """Get the direction from the axis index."""
        return [Direction3D.X, Direction3D.Y, Direction3D.Z][i]

    def __str__(self) -> str:
        return self.name


class PipeType(Enum):
    """Valid pipe types in the library."""
    # pipes without H
    OZX = "ozx"
    OXZ = "oxz"
    XOZ = "xoz"
    ZOX = "zox"
    XZO = "xzo"
    ZXO = "zxo"
    # pipes with H
    OZXH = "ozxh"
    OXZH = "oxzh"
    ZOXH = "zoxh"
    XOZH = "xozh"
    ZXOH = "zxoh"
    XZOH = "xzoh"

    @property
    def has_hadamard(self) -> bool:
        """Check if the block type has a hadamard transition."""
        return "h" in self.value

    @property
    def direction(self) -> Direction3D:
        """Return the direction of the pipe."""
        return [Direction3D.X, Direction3D.Y, Direction3D.Z][self.value.index("o")]

    def get_color_at_side(self, src_side: bool = True) -> Color3D:
        """Get the color of the pipe at the given side."""
        if not self.has_hadamard or src_side:
            return Color3D.from_string(self.value[:3])
        return Color3D.from_string(self.value[:3], flip_xz=True)


BlockType = CubeType | PipeType
"""Valid block types in the library."""


def parse_block_type_from_str(block_type: str) -> BlockType:
    """Parse a block type from a string."""
    if 'o' in block_type:
        return PipeType(block_type.lower())
    else:
        return CubeType(block_type.lower())


@dataclass(frozen=True)
class Cube:
    """A block representing the computational unit in a 3D spacetime diagram."""
    position: Position3D
    cube_type: CubeType


@dataclass(frozen=True)
class Pipe:
    """A block connecting two cubes in a 3D spacetime diagram.

    The pipe represents the idle or merge/split lattice surgery operation on logical
    qubits depending on its direction.
    """
    u: Cube
    v: Cube
    pipe_type: PipeType

    def __post_init__(self) -> None:
        # Ensure position of u is less than v
        u, v = self.u, self.v
        if self.u.position > self.v.position:
            object.__setattr__(self, "u", v)
            object.__setattr__(self, "v", u)


_CUBE_DATA_KEY = "cube_data"
_PIPE_DATA_KEY = "pipe_data"


class BlockGraph:
    def __init__(self, name: str) -> None:
        """An undirected graph representation of a 3D spacetime defect diagram with
        the block structures explicitly defined."""
        self._name = name
        self._graph = nx.Graph()

    @property
    def name(self) -> str:
        """The name of the graph."""
        return self._name

    @property
    def num_cubes(self) -> int:
        """The number of cubes in the graph."""
        return self._graph.number_of_nodes()

    @property
    def num_pipes(self) -> int:
        """The number of pipes in the graph."""
        return self._graph.number_of_edges()

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
        self._graph.add_node(position, _CUBE_DATA_KEY=Cube(position, cube_type))

    def add_pipe(self, u: Position3D, v: Position3D, pipe_type: PipeType) -> None:
        """Add a pipe to the graph.

        Args:
            u: The position of the first cube.
            v: The position of the second cube.
            pipe_type: The type of the pipe.
        """
        if u not in self._graph or v not in self._graph:
            raise TQECException("Both cubes must exist in the graph.")
        if not u.is_nearby(v):
            raise TQECException("The two cubes must be nearby in the 3D space to be connected.")
        u_node = self._graph.nodes[u][_CUBE_DATA_KEY]
        v_node = self._graph.nodes[v][_CUBE_DATA_KEY]
        self._graph.add_edge(u, v, _PIPE_DATA_KEY=(u_node, v_node, PipeType))

    def get_cube(self, position: Position3D) -> Cube | None:
        """Get the cube by position."""
        if position not in self._graph:
            return None
        return self._graph.nodes[position][_CUBE_DATA_KEY]

    def get_pipe(self, u: Position3D, v: Position3D) -> Pipe | None:
        """Get the pipe by its endpoint cube positions."""
        if not self._graph.has_edge(u, v):
            return None
        return self._graph.edges[u, v][_CUBE_DATA_KEY]

    def check_validity(self, allow_virtual_node: bool = True) -> None:
        """Check the validity of the block structures represented by the graph.

        Refer to the Fig.9 in arXiv:2404.18369. Currently, we only check the constraints
        d, f and g in the figure:
            1. No 3D corner: all the pipes are within the same plane.
            2. Match color at pass-through: the pipes and cube have the same color at the pass-through.
            3. Match color at turn: the pipes and cube have the same color at the bent side of the turn.

        Args:
            allow_virtual_node: Whether to allow the virtual node in the graph. A virtual node is an open
                port of a pipe. It is not a physical cube but a placeholder for the pipe to connect to the
                boundary of the graph. Default is True.
        """
        if not allow_virtual_node and any(cube.cube_type.is_virtual for cube in self.cubes):
            raise TQECException("The graph contains a virtual node.")
        for cube in self.cubes:
            self._check_validity_locally_at_cube(cube)

    def _check_validity_locally_at_cube(self, cube: Cube) -> None:
        """Check the validity of the block structures locally at a cube."""
        # Skip the virtual cube
        if cube.cube_type.is_virtual:
            return
        pipes_by_direction: dict[Direction3D, list[Pipe]] = {}
        for _, _, data in self._graph.edges(cube.position, data=True):
            pipe = data[_PIPE_DATA_KEY]
            pipes_by_direction.setdefault(pipe.pipe_type.direction, []).append(pipe)
        pipe_directions = set(pipes_by_direction.keys())
        # 1. No 3D corner
        if len(pipe_directions) == 3:
            raise TQECException(f"Cube at {cube.position} has a 3D corner.")
        # 2. Match color at pass-through
        cube_color = cube.cube_type.get_color()
        for direction, pipes in pipes_by_direction.items():
            if not all(pipe.pipe_type.get_color_at_side(pipe.u == cube).match(cube_color) for pipe in pipes):
                raise TQECException(f"Cube at {cube.position} has unmatched color at pass-through along {direction} direction.")
        # 3. Match color at turn
        if len(pipe_directions) == 2:
            # since we have checked the pass-throught match
            # we only have to check that the surrounding walls at the turn plane have the same color
            normal_direction_to_corner_plane = ty.cast(Direction3D, cube.cube_type.normal_direction_to_corner_plane())
            if normal_direction_to_corner_plane in pipe_directions:
                raise TQECException(f"Cube at {cube.position} has unmatched color at turn.")

    def to_zx_graph(self, name: str = "") -> ZXGraph:
        """Convert the block graph to a ZX graph."""
        zx_graph = ZXGraph(name if name else self.name + "_ZX")
        for cube in self.cubes:
            zx_graph.add_node(cube.position, cube.cube_type.to_zx_node_type())
        for pipe in self.pipes:
            zx_graph.add_edge(pipe.u.position, pipe.v.position, pipe.pipe_type.has_hadamard)
        return zx_graph

    @staticmethod
    def from_zx_graph(zx_graph: ZXGraph, name: str = "", check_validity: bool = True) -> "BlockGraph":
        """Construct a block graph from a ZX graph.

        The ZX graph includes the minimal information required to construct the block graph,
        but not guaranteed to admit a valid block structure. The block structure will be inferred
        from the ZX graph and validated.

        Args:
            zx_graph: The base ZX graph to construct the block graph.
            name: The name of the new block graph.
            check_validity: Whether to check the validity of the block graph after construction. Default is True.

        Returns:
            The constructed block graph.
        """
        pass
