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
