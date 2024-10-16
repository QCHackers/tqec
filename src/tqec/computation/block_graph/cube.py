from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from tqec.position import Position3D
from tqec.computation.block_graph.enums import CubeType, PipeType

BlockType = Union[CubeType, PipeType]
"""Valid block types in the library."""


@dataclass(frozen=True)
class Cube:
    """A block representing the computational unit in a 3D spacetime
    diagram."""

    position: Position3D
    cube_type: CubeType

    @property
    def is_virtual(self) -> bool:
        """Check if the cube is virtual, i.e. an open port."""
        return self.cube_type == CubeType.VIRTUAL

    def shift_position_by(self, dx: int = 0, dy: int = 0, dz: int = 0) -> Cube:
        """Shift the position of the cube in the 3D space."""
        return Cube(
            self.position.shift_by(dx, dy, dz),
            self.cube_type,
        )
