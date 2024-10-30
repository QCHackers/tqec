from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import astuple, dataclass
from enum import Enum

from tqec.computation.zx_graph import ZXKind, ZXNode
from tqec.exceptions import TQECException
from tqec.position import Direction3D, Position3D


class ZXBasis(Enum):
    """Z or X basis."""

    Z = "Z"
    X = "X"

    def with_zx_flipped(self) -> ZXBasis:
        """Get the basis with the Z/X flipped."""
        return ZXBasis.Z if self == ZXBasis.X else ZXBasis.X

    def __str__(self) -> str:
        return self.value


class CubeKind(ABC):
    """Base class for the cube types."""

    @abstractmethod
    def to_zx_kind(self) -> ZXKind:
        """Convert the cube kind to a ZX node kind."""
        pass


@dataclass(frozen=True)
class ZXCube(CubeKind):
    """Cube kind representing the cube surrounded by all X/Z basis walls."""

    x: ZXBasis
    y: ZXBasis
    z: ZXBasis

    def as_tuple(self) -> tuple[ZXBasis, ZXBasis, ZXBasis]:
        return astuple(self)

    def __post_init__(self) -> None:
        if self.x == self.y == self.z:
            raise TQECException(
                "The cube kind with all the same basis walls is not allowed."
            )

    def __str__(self) -> str:
        return f"{self.x.value}{self.y.value}{self.z.value}"

    @staticmethod
    def all_kinds() -> list[ZXCube]:
        """Return all the possible `ZXCube` kinds."""
        return [ZXCube.from_str(s) for s in ["ZXZ", "XZZ", "ZXX", "XZX", "XXZ", "ZZX"]]

    @staticmethod
    def from_str(string: str) -> ZXCube:
        """Create a cube kind from the string representation."""
        return ZXCube(*map(ZXBasis, string.upper()))

    @property
    def cube_basis(self) -> ZXBasis:
        """Return the basis of the cube.

        A cube has only one Z/X basis wall is a Z/X basis cube.
        """
        if sum(basis == ZXBasis.Z for basis in astuple(self)) == 1:
            return ZXBasis.Z
        return ZXBasis.X

    def to_zx_kind(self) -> ZXKind:
        return ZXKind(self.cube_basis.value)

    @property
    def normal_direction(self) -> Direction3D:
        """Get the direction in which the wall basis is the same as the cube
        basis."""
        return Direction3D(astuple(self).index(self.cube_basis))

    @staticmethod
    def from_normal_basis(basis: ZXBasis, direction: Direction3D) -> ZXCube:
        """Create a cube kind with the given normal basis and direction."""
        bases = [basis.with_zx_flipped() for _ in range(3)]
        bases[direction.value] = basis
        return ZXCube(*bases)

    @property
    def is_spatial_junction(self) -> bool:
        """Check if the cube is a spatial junction."""
        return self.x == self.y

    def get_basis_along(self, direction: Direction3D) -> ZXBasis:
        """Get the basis of the wall in the given direction."""
        return self.as_tuple()[direction.value]


class Port(CubeKind):
    """Cube kind representing the open ports in the block graph.

    The open ports correspond to the input/output of the computation represented by the block graph.
    They will have no effect on the functionality of the logical computation itself and should be
    invisible when visualizing the computation model.
    """

    def __str__(self) -> str:
        return "PORT"

    def to_zx_kind(self) -> ZXKind:
        return ZXKind.P

    def __hash__(self) -> int:
        return hash(Port)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Port)


class YCube(CubeKind):
    """Cube kind representing the Y-basis initialization/measurements."""

    def __str__(self) -> str:
        return "Y"

    def to_zx_kind(self) -> ZXKind:
        return ZXKind.Y

    def __hash__(self) -> int:
        return hash(YCube)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, YCube)


@dataclass(frozen=True)
class Cube:
    """A block representing the computational unit in a 3D logical computation."""

    position: Position3D
    kind: CubeKind
    label: str | None = None

    def __post_init__(self) -> None:
        if self.is_port and self.label is None:
            raise TQECException("A port cube must have a port label.")

    def __str__(self) -> str:
        return f"{self.kind}{self.position}"

    @property
    def is_zx_cube(self) -> bool:
        """Check if the cube is a ZX cube."""
        return isinstance(self.kind, ZXCube)

    @property
    def is_port(self) -> bool:
        """Check if the cube is an open port."""
        return isinstance(self.kind, Port)

    @property
    def is_y_cube(self) -> bool:
        return isinstance(self.kind, YCube)

    @property
    def is_spatial_junction(self) -> bool:
        """Check if the cube is a spatial junction."""
        return isinstance(self.kind, ZXCube) and self.kind.is_spatial_junction

    def to_zx_node(self) -> ZXNode:
        """Convert the cube to a ZX node."""
        return ZXNode(self.position, self.kind.to_zx_kind(), self.label)

    def shift_position_by(self, dx: int = 0, dy: int = 0, dz: int = 0) -> Cube:
        """Shift the position of the cube."""
        return Cube(self.position.shift_by(dx, dy, dz), self.kind, self.label)
