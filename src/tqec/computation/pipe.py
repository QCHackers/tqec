from __future__ import annotations

from dataclasses import dataclass
from typing import Generator

from tqec.exceptions import TQECException
from tqec.position import Direction3D
from tqec.computation.cube import Cube, ZXBasis, ZXCube


@dataclass(frozen=True)
class PipeKind:
    x: ZXBasis | None
    y: ZXBasis | None
    z: ZXBasis | None
    has_hadamard: bool = False

    def __post_init__(self) -> None:
        if sum(basis is None for basis in (self.x, self.y, self.z)) != 1:
            raise TQECException("Exactly one basis must be None for a pipe.")
        if len({self.x, self.y, self.z}) != 3:
            raise TQECException("Pipe must have different basis walls.")

    def __str__(self) -> str:
        return "".join(
            basis.value if basis is not None else "O"
            for basis in (self.x, self.y, self.z)
        ) + ("H" if self.has_hadamard else "")

    @staticmethod
    def from_str(string: str) -> PipeKind:
        """Create a pipe kind from the string representation."""
        string = string.upper()
        has_hadamard = len(string) == 4 and string[3] == "H"
        return PipeKind(
            *[ZXBasis(s) if s != "O" else None for s in string[:3]],
            has_hadamard=has_hadamard,
        )

    @property
    def direction(self) -> Direction3D:
        """Get the connection direction of the pipe."""
        return Direction3D(str(self).index("O"))

    def get_basis_along(
        self, direction: Direction3D, at_head: bool = True
    ) -> ZXBasis | None:
        """Get the basis of the kind in the given direction.

        Args:
            direction: The direction of the basis.
            at_head: If True, get the basis at the head side of the pipe. Otherwise,
                get the basis at the tail of the pipe. The head side will have the
                opposite basis as the tail if the pipe has hadamard transition.

        Returns:
            None if the basis is not defined in the direction, i.e. the direction is
            the same as the pipe direction. Otherwise, the basis in the direction at
            the specified side.
        """
        if direction == self.direction:
            return None
        head_basis = ZXBasis(str(self)[direction.value])
        if not at_head and self.has_hadamard:
            return head_basis.with_zx_flipped()

    @property
    def is_temporal(self) -> bool:
        """Check if the pipe is temporal."""
        return self.z is None

    @property
    def is_spatial(self) -> bool:
        """Check if the pipe is spatial."""
        return not self.is_temporal


@dataclass(frozen=True)
class Pipe:
    """A block connecting two cubes in a 3D spacetime diagram.

    The pipe represents the idle or merge/split lattice surgery
    operation on logical qubits depending on its direction.

    Attributes:
        u: The first cube. The position of u will be guaranteed to be less than v.
        v: The second cube. The position of v will be guaranteed to be greater than u.
        kind: The type of the pipe.
    """

    u: Cube
    v: Cube
    kind: PipeKind

    def __post_init__(self) -> None:
        if not self.u.position.is_neighbour(self.v.position):
            raise TQECException("A pipe must connect two nearby cubes.")
        # Ensure position of u is less than v
        u, v = self.u, self.v
        if self.u.position > self.v.position:
            object.__setattr__(self, "u", v)
            object.__setattr__(self, "v", u)

    @property
    def direction(self) -> Direction3D:
        """Get the direction of the pipe."""
        return self.kind.direction

    def validate(self) -> None:
        """Check the color of the pipe can match the cubes at its endpoints."""
        for cube in (self.u, self.v):
            if cube.is_port or cube.is_y_cube:
                continue
            assert isinstance(cube.kind, ZXCube)
            for direction in Direction3D.all_directions():
                if direction == self.direction:
                    continue
                cube_basis = cube.kind.get_basis_along(direction)
                pipe_basis = self.kind.get_basis_along(direction, cube == self.u)
                if cube_basis != pipe_basis:
                    raise TQECException(
                        f"The pipe has color does not match the cube {cube}."
                    )

    def __iter__(self) -> Generator[Cube]:
        yield self.u
        yield self.v

    def shift_position_by(self, dx: int = 0, dy: int = 0, dz: int = 0) -> Pipe:
        """Shift the position of the pipe by the given displacement."""
        return Pipe(
            self.u.shift_position_by(dx, dy, dz),
            self.v.shift_position_by(dx, dy, dz),
            self.kind,
        )
