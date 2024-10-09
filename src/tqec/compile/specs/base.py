from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tqec.compile.block import CompiledBlock
from tqec.compile.specs.enums import JunctionArms
from tqec.computation.block_graph.cube import Cube
from tqec.computation.block_graph.enums import CubeType
from tqec.computation.block_graph.graph import BlockGraph
from tqec.exceptions import TQECException


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


class SpecRule(Protocol):
    """Protocol for returning a `CompiledBlock` based on a `CubeSpec`.

    Users can define their own rules for generating `CompiledBlock`s based on the
    `CubeSpec` provided and register them during compilation.
    """

    def __call__(self, spec: CubeSpec) -> CompiledBlock:
        """Get a `CompiledBlock` instance from a `CubeSpec`.

        Args:
            spec: Specification of the cube in the block graph.

        Returns:
            a `CompiledBlock` based on the provided `CubeSpec`.
        """
        ...
