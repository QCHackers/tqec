from __future__ import annotations

from dataclasses import astuple
from enum import Enum
from typing import Literal, cast

from tqec.exceptions import TQECException
from tqec.position import Direction3D
from tqec.computation.block_graph.color import Color, Color3D
from tqec.computation.block_graph.cube import CubeKind


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
    ) -> CubeKind:
        """Infer the cube type at the side of the pipe."""
        color = self.get_color_at_side(src_side_if_h_pipe).push_color_at_direction(
            self.direction, Color.Z if is_z_cube else Color.X
        )
        return CubeKind.from_color(color)

    def temporal_basis(self) -> Literal["X", "Z"]:
        if self.direction == Direction3D.Z:
            raise TQECException("Cannot get the temporal basis on a temporal pipe.")
        # Because this is not a temporal pipe, we know for sure
        # that there is no "o" in the Z direction. Also, "h" can
        # not appear in the first 3 entries, so self.value[2] is
        # either "x" or "z".
        return cast(Literal["X", "Z"], self.value[2].upper())
