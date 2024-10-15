from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from tqec.compile.block import CompiledBlock
from tqec.compile.specs.enums import JunctionArms
from tqec.computation.block_graph.cube import Cube
from tqec.computation.block_graph.enums import CubeType, PipeType
from tqec.computation.block_graph.graph import BlockGraph
from tqec.exceptions import TQECException
from tqec.plaquette.plaquette import Plaquettes


@dataclass(frozen=True)
class CubeSpec:
    """Specification of a cube in a block graph.

    The template of the `CompiledBlock` will be determined based on the specification.
    This class can be used as a key to look up the corresponding `CompiledBlock` before
    applying the substitution rules.

    Attributes:
        cube_type: Type of the cube.
        junction_arms: Flag indicating the spatial directions the cube connects to the
            adjacent cubes. This is useful for spatial junctions (XXZ and ZZX) where
            the arms can determine the template used to implement the cube.
    """

    cube_type: CubeType
    junction_arms: JunctionArms = JunctionArms.NONE

    def __post_init__(self) -> None:
        # arm_flags is not None iff cube_type is ZZX or XXZ(Spatial Junctions)
        if (self.is_spatial_junction) ^ (self.junction_arms != JunctionArms.NONE):
            raise TQECException(
                "junction_arms is not NONE if and only if cube_type is spatial junctions(ZZX or XXZ)."
            )

    @property
    def is_spatial_junction(self) -> bool:
        return self.cube_type.is_spatial_junction

    @staticmethod
    def from_cube(cube: Cube, graph: BlockGraph) -> CubeSpec:
        """Returns the cube spec from a cube in a block graph."""
        if cube.cube_type not in [CubeType.ZZX, CubeType.XXZ]:
            return CubeSpec(cube.cube_type)
        pos = cube.position
        junction_arms = JunctionArms.NONE
        for flag, shift in JunctionArms.get_map_from_arm_to_shift().items():
            if graph.get_pipe(pos, pos.shift_by(*shift)) is not None:
                junction_arms |= flag
        return CubeSpec(cube.cube_type, junction_arms)


class CompiledBlockBuilder(Protocol):
    """Protocol for building a `CompiledBlock` based on a `CubeSpec`."""

    def __call__(self, spec: CubeSpec) -> CompiledBlock:
        """Build a `CompiledBlock` instance from a `CubeSpec`.

        Args:
            spec: Specification of the cube in the block graph.

        Returns:
            a `CompiledBlock` based on the provided `CubeSpec`.
        """
        ...


@dataclass(frozen=True)
class PipeSpec:
    """Specification of a pipe in a block graph.

    Attributes:
        spec1: the cube specification of the first cube. By convention, the cube
            corresponding to `spec1` should have a smaller position than the cube
            corresponding to `spec2`.
        spec2: the cube specification of the second cube.
        pipe_type: the type of the pipe connecting the two cubes.
    """

    spec1: CubeSpec
    spec2: CubeSpec
    pipe_type: PipeType


@dataclass(frozen=True)
class Substitution:
    """Specification of how to substitute plaquettes in the two `CompiledBlock`s
    connected by a pipe.

    When applying the substitution, the plaquettes in the map will be used to
    update the corresponding layer in the `CompiledBlock`.

    Both the source and destination maps are indexed by the layer index in the
    `CompiledBlock`. The index can be negative, which means the layer is counted
    from the end of the layers list.

    Attributes:
        src: a mapping from the index of the layer in the source `CompiledBlock` to
            the plaquettes that should be used to update the layer.
        dst: a mapping from the index of the layer in the destination `CompiledBlock`
            to the plaquettes that should be used to update
    """

    src: Mapping[int, Plaquettes]
    dst: Mapping[int, Plaquettes]


class SubstitutionBuilder(Protocol):
    """Protocol for building the `Substitution` based on a `PipeSpec`."""

    def __call__(self, spec: PipeSpec) -> Substitution:
        """Build a `Substitution` instance from a `PipeSpec`.

        Args:
            spec: Specification of the pipe in the block graph.

        Returns:
            a `Substitution` based on the provided `PipeSpec`.
        """
        ...
