"""Defines the :py:class:`~tqec.computation.pipe.Pipe` class."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generator

from tqec.exceptions import TQECException
from tqec.position import Direction3D
from tqec.computation.cube import Cube, ZXBasis, ZXCube


@dataclass(frozen=True)
class PipeKind:
    """The kind of a pipe in the block graph.

    Looking at the head of the pipe, i.e. the side which has smaller position,
    the kind is determined by the wall bases there together with whether the
    pipe has a hadamard transition. The basis along the direction of the pipe
    should be None.

    Attributes:
        x: At the head of the pipe, looking at the pipe along the x-axis, the basis
           of the walls observed. Can be None if the pipe connects two cubes along
           the x-axis.
        y: At the head of the pipe, looking at the pipe along the y-axis, the basis
           of the walls observed. Can be None if the pipe connects two cubes along
           the y-axis.
        z: At the head of the pipe, looking at the pipe along the z-axis, the basis
           of the walls observed. Can be None if the pipe connects two cubes along
           the z-axis.
        has_hadamard: Whether the pipe has a hadamard transition.
    """

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
        """Create a pipe kind from the string representation.

        The string should be a 3-character or 4-character string. The first 3
        characters represent the basis of the walls at the head of the pipe
        along the x, y, and z axes. If there is no wall along an axis, i.e.
        the pipe connects two cubes along that axis, the character should be
        "O" for open boundary. The last character, if exists, should be "H"
        to indicate the pipe has a hadamard transition.

        Args:
            string: The string representation of the pipe kind.

        Returns:
            The pipe kind represented by the string.
        """
        string = string.upper()
        has_hadamard = len(string) == 4 and string[3] == "H"
        return PipeKind(
            *(ZXBasis(s) if s != "O" else None for s in string[:3]),  # type: ignore
            has_hadamard=has_hadamard,
        )

    @property
    def direction(self) -> Direction3D:
        """The direction along which the pipe connects the cubes."""
        return Direction3D(str(self).index("O"))

    def get_basis_along(
        self, direction: Direction3D, at_head: bool = True
    ) -> ZXBasis | None:
        """Get the wall basis of the pipe in the specified direction.

        Args:
            direction: The direction along which to get the basis.
            at_head: If True, get the basis at the head of the pipe, i.e. the side
                which has smaller position. Otherwise, get the basis at the tail of
                the pipe. This matters when the pipe has hadamard transition.

        Returns:
            None if the direction is the same as the pipe direction. Otherwise, the
            basis of the wall in the specified direction.
        """
        if direction == self.direction:
            return None
        head_basis = ZXBasis(str(self)[direction.value])
        if not at_head and self.has_hadamard:
            return head_basis.with_zx_flipped()
        return head_basis

    @property
    def is_temporal(self) -> bool:
        """Whether the pipe is temporal, i.e. connects two cubes along the Z
        axis."""
        return self.z is None

    @property
    def is_spatial(self) -> bool:
        """Whether the pipe is spatial, i.e. connects two cubes along the X or
        Y axis."""
        return not self.is_temporal

    @staticmethod
    def _from_cube_kind(
        cube_kind: ZXCube,
        direction: Direction3D,
        cube_at_head: bool,
        has_hadamard: bool = False,
    ) -> PipeKind:
        """Infer the pipe kind from the endpoint cube kind and the pipe
        direction.

        Args:
            cube_kind: The kind of the cube at the endpoint of the pipe.
            direction: The direction of the pipe.
            cube_at_head: Whether the cube at the head of the pipe, i.e. the
                side with smaller position.
            has_hadamard: Whether the pipe has a hadamard transition.

        Returns:
            The inferred pipe kind.
        """
        bases: list[ZXBasis]
        if not cube_at_head and has_hadamard:
            bases = [basis.with_zx_flipped() for basis in cube_kind.as_tuple()]
        else:
            bases = list(cube_kind.as_tuple())
        bases_str = [basis.value for basis in bases]
        bases_str[direction.value] = "O"
        if has_hadamard:
            bases_str.append("H")
        return PipeKind.from_str("".join(bases_str))


@dataclass(frozen=True)
class Pipe:
    """A block connecting two :py:class:`~tqec.computation.cube.Cube` objects.

    The pipes connect the cubes in the block graph. Topologically, the pipes
    open the boundaries of the cubes and wire them together to form the topological
    structure representing the computation. In the circuit level, the pipes
    make modifications to the blocks of operations represented by the cubes.
    Importantly, the pipes themselves do not occupy spacetime volume.

    WARNING: The attributes `u` and `v` will be ordered to ensure the position of `u`
    is less than `v`.

    Attributes:
        u: The cube at the head of the pipe. The position of u will be guaranteed to be less than v.
        v: The cube at the tail of the pipe. The position of v will be guaranteed to be greater than u.
        kind: The kind of the pipe.
    """

    u: Cube
    v: Cube
    kind: PipeKind

    def __post_init__(self) -> None:
        u, v = self.u, self.v
        p1, p2 = u.position, v.position
        shift = [0, 0, 0]
        shift[self.kind.direction.value] = 1
        if not p1.shift_by(*shift) == p2 and not p2.shift_by(*shift) == p1:
            raise TQECException(
                f"The pipe must connect two nearby cubes in direction {self.kind.direction}."
            )

        # Ensure position of u is less than v
        if p1 > p2:
            object.__setattr__(self, "u", v)
            object.__setattr__(self, "v", u)

    @staticmethod
    def from_cubes(u: Cube, v: Cube) -> Pipe:
        """Construct a pipe connecting two cubes and infer the pipe kind.

        Args:
            u: The first cube.
            v: The second cube.

        Returns:
            The pipe connecting the two cubes.

        Raises:
            TQECException: If the cubes are not neighbours or both of them are not ZX cubes.
            TQECException: If kind of the pipe cannot be inferred from the cubes.
        """
        if not u.is_zx_cube and not v.is_zx_cube:
            raise TQECException(
                "At least one cube must be a ZX cube to infer the pipe kind."
            )
        u, v = (u, v) if u.position < v.position else (v, u)
        if not u.position.is_neighbour(v.position):
            raise TQECException("The cubes must be neighbours to create a pipe.")
        direction = next(
            d
            for d in Direction3D.all_directions()
            if u.position.shift_in_direction(d, 1) == v.position
        )

        # One cube is not a ZX cube
        if not u.is_zx_cube or not v.is_zx_cube:
            infer_from = u if u.is_zx_cube else v
            cube_kind = infer_from.kind
            assert isinstance(cube_kind, ZXCube)
            pipe_kind = PipeKind._from_cube_kind(cube_kind, direction, infer_from == u)
            return Pipe(u, v, pipe_kind)

        # Both cubes are ZX cubes
        assert isinstance(u.kind, ZXCube) and isinstance(v.kind, ZXCube)
        has_hadamard = {
            u.kind.get_basis_along(d) != v.kind.get_basis_along(d)
            for d in Direction3D.all_directions()
            if d != direction
        }
        if len(has_hadamard) == 2:
            raise TQECException("Cannot infer a valid pipe kind from the cubes.")
        pipe_kind = PipeKind._from_cube_kind(
            u.kind, direction, True, has_hadamard.pop()
        )
        return Pipe(u, v, pipe_kind)

    @property
    def direction(self) -> Direction3D:
        """The direction along which the pipe connects the cubes."""
        return self.kind.direction

    def check_compatible_with_cubes(self) -> None:
        """Check if the pipe is compatible with the cubes it connects.

        For compatibility, each cube (head and tail) must match the pipe's basis
        along each direction, except for the direction of the pipe, if the cube is
        of type :py:class:`~tqec.computation.cube.ZXCube`.

        Raises:
            TQECException: If the pipe is not compatible with the cubes.
        """
        for cube in self:
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
                        f"The pipe is not compatible with the cube {cube} along {direction} direction."
                    )

    def __iter__(self) -> Generator[Cube]:
        yield self.u
        yield self.v
