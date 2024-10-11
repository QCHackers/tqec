from __future__ import annotations

from dataclasses import astuple
from enum import Enum
from typing import Literal, cast

from tqec.exceptions import TQECException
from tqec.position import Direction3D
from tqec.computation.block_graph.color import Color, Color3D
from tqec.computation.zx_graph import NodeType


class CubeType(Enum):
    """Valid cube types in the library."""

    ZXX = "zxx"
    XZX = "xzx"
    XXZ = "xxz"
    XZZ = "xzz"
    ZXZ = "zxz"
    ZZX = "zzx"
    # Y basis measurement
    Y = "y"
    # Virtual cube for open port
    VIRTUAL = "virtual"

    @property
    def is_spatial_junction(self) -> bool:
        return self in [CubeType.ZZX, CubeType.XXZ]

    def to_zx_node_type(self) -> NodeType:
        """Convert the cube type to a ZX node type."""
        if self == CubeType.VIRTUAL:
            return NodeType.V
        if self.value.count("z") == 2:
            return NodeType.Z
        if self.value.count("x") == 2:
            return NodeType.X
        raise TQECException(
            f"Conversion from {self} to ZX node type is not supported yet."
        )

    def get_color(self) -> Color3D:
        """Get the color of the block."""
        return Color3D.from_string(self.value)

    @staticmethod
    def from_color(color: Color3D) -> CubeType:
        """Get the cube type from the color."""
        if color.is_null:
            return CubeType.VIRTUAL
        if any(c.is_null for c in astuple(color)):
            raise TQECException("All the color must be defined for a non-virtual cube.")
        return CubeType("".join(c.value for c in astuple(color)).lower())

    def normal_direction_to_corner_plane(self) -> Direction3D:
        """If the cube is at a corner, return the normal direction to the
        corner plane.

        Due to the color match rule at the corner turn, the corner plane
        can be inferred from the type of the cube.
        """
        if self == CubeType.VIRTUAL:
            raise TQECException("Cannot infer the corner plane for a virtual cube.")
        if self.value.count("z") == 2:
            return Direction3D.from_axis_index(self.value.index("x"))
        return Direction3D.from_axis_index(self.value.index("z"))

    def infer_pipe_type_at_direction(
        self,
        direction: Direction3D,
        src_side_if_h_pipe: bool = True,
        has_hadamard: bool = False,
    ) -> PipeType:
        """Infer the pipe type connecting this cube at some direction with the
        color match rule."""
        if self == CubeType.VIRTUAL:
            raise TQECException("Cannot infer the pipe type for a virtual cube.")
        color = self.get_color().pop_color_at_direction(direction)
        return PipeType.from_color_at_side(color, src_side_if_h_pipe, has_hadamard)


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
        return Direction3D.all()[self.value.index("o")]

    def get_color_at_side(self, src_side_if_h_pipe: bool = True) -> Color3D:
        """Get the color of the pipe at the given side."""
        if not self.has_hadamard or src_side_if_h_pipe:
            return Color3D.from_string(self.value[:3])
        return Color3D.from_string(self.value[:3], flip_xz=True)

    @staticmethod
    def from_color_at_side(
        color: Color3D, src_side_if_h_pipe: bool = True, has_hadamard: bool = False
    ) -> PipeType:
        """Get the pipe type from the color at one side."""
        if not sum(c.is_null for c in astuple(color)) == 1:
            raise TQECException(
                "Exactly one color must be undefined for a pipe along the pipe direction."
            )
        pipe_color = []
        for c in astuple(color):
            if c.is_null:
                pipe_color.append("o")
            elif has_hadamard and not src_side_if_h_pipe:
                pipe_color.append("x" if c == Color.Z else "z")
            else:
                pipe_color.append(c.value)
        if has_hadamard:
            pipe_color.append("h")
        return PipeType("".join(pipe_color).lower())

    def infer_cube_type_at_side(
        self, src_side_if_h_pipe: bool = True, is_z_cube: bool = True
    ) -> CubeType:
        """Infer the cube type at the side of the pipe."""
        color = self.get_color_at_side(src_side_if_h_pipe).push_color_at_direction(
            self.direction, Color.Z if is_z_cube else Color.X
        )
        return CubeType.from_color(color)

    def temporal_basis(self) -> Literal["X", "Z"]:
        if self.direction == Direction3D.Z:
            raise TQECException("Cannot get the temporal basis on a temporal pipe.")
        # Because this is not a temporal pipe, we know for sure
        # that there is no "o" in the Z direction. Also, "h" can
        # not appear in the first 3 entries, so self.value[2] is
        # either "x" or "z".
        return cast(Literal["X", "Z"], self.value[2].upper())
