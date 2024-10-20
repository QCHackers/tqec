from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tqec.computation.zx_graph import ZXKind, ZXNode
from tqec.position import Position3D


class CubeKind(Enum):
    """Valid cube types in the library."""

    # Regular cubes
    ZXX = "ZXX"
    XZX = "XZX"
    XZZ = "XZZ"
    ZXZ = "ZXZ"
    # Spatial junctions
    XXZ = "XXZ"
    ZZX = "ZZX"
    # Y cube
    Y = "Y"
    # Port
    P = "PORT"

    def to_zx_kind(self) -> ZXKind:
        """Convert the cube kind to a ZX node kind."""
        if self == CubeKind.P:
            return ZXKind.P
        if self == CubeKind.Y:
            return ZXKind.Y
        if self.value.count("z") == 2:
            return ZXKind.X
        # self.value.count("x") == 2
        return ZXKind.Z

    # @property
    # def temporal_basis(self) -> Literal["X", "Z", "Y"] | None:
    #     if self.is_y:
    #         return "Y"
    #     if self.is_virtual:
    #         return None
    #     return cast(Literal["X", "Z"], self.value[2].upper())
    #
    # def get_color(self) -> Color3D:
    #     """Get the color of the block."""
    #     return Color3D.from_string(self.value)
    #
    # @staticmethod
    # def from_color(color: Color3D) -> CubeKind:
    #     """Get the cube type from the color."""
    #     if color.is_null:
    #         return CubeKind.VIRTUAL
    #     if any(c.is_null for c in astuple(color)):
    #         raise TQECException("All the color must be defined for a non-virtual cube.")
    #     return CubeKind("".join(c.value for c in astuple(color)).lower())
    #
    # def normal_direction_to_corner_plane(self) -> Direction3D:
    #     """If the cube is at a corner, return the normal direction to the
    #     corner plane.
    #
    #     Due to the color match rule at the corner turn, the corner plane
    #     can be inferred from the type of the cube.
    #     """
    #     if self == CubeKind.VIRTUAL:
    #         raise TQECException("Cannot infer the corner plane for a virtual cube.")
    #     if self.value.count("z") == 2:
    #         return Direction3D.from_axis_index(self.value.index("x"))
    #     return Direction3D.from_axis_index(self.value.index("z"))
    #
    # def infer_pipe_type_at_direction(
    #     self,
    #     direction: Direction3D,
    #     src_side_if_h_pipe: bool = True,
    #     has_hadamard: bool = False,
    # ) -> PipeType:
    #     """Infer the pipe type connecting this cube at some direction with the
    #     color match rule."""
    #     if self == CubeKind.VIRTUAL:
    #         raise TQECException("Cannot infer the pipe type for a virtual cube.")
    #     color = self.get_color().pop_color_at_direction(direction)
    #     return PipeType.from_color_at_side(color, src_side_if_h_pipe, has_hadamard)


@dataclass(frozen=True)
class Cube:
    """A block representing the computational unit in a 3D spacetime
    diagram."""

    position: Position3D
    kind: CubeKind

    @property
    def is_port(self) -> bool:
        """Check if the cube is an open port."""
        return self.kind == CubeKind.P

    @property
    def is_regular(self) -> bool:
        """Check if the cube is a regular cube."""
        return self.kind in [
            CubeKind.ZXX,
            CubeKind.XZX,
            CubeKind.XZZ,
            CubeKind.ZXZ,
        ]

    @property
    def is_spatial_junction(self) -> bool:
        """Check if the cube is a spatial junction."""
        return self.kind in [CubeKind.ZZX, CubeKind.XXZ]

    @property
    def is_y_cube(self) -> bool:
        return self.kind == CubeKind.Y

    def to_zx_node(self) -> ZXNode:
        """Convert the cube to a ZX node."""
        return ZXNode(self.position, self.kind.to_zx_kind())
