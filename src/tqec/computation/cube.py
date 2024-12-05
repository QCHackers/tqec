"""Defines the :py:class:`~tqec.computation.cube.Cube` class."""

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
        """Return the flipped basis, i.e. ``Z -> X``, ``X -> Z``."""
        return ZXBasis.Z if self == ZXBasis.X else ZXBasis.X

    def __str__(self) -> str:
        return self.value


class CubeKind(ABC):
    """Base class for the kinds of cubes in the block graph."""

    @abstractmethod
    def to_zx_kind(self) -> ZXKind:
        """Return the corresponding
        :py:class:`~tqec.computation.zx_graph.ZXKind` of the cube kind.

        Returns:
            The corresponding ZX kind of the cube kind.
        """
        pass


@dataclass(frozen=True)
class ZXCube(CubeKind):
    """The kind of cubes consisting of only X or Z basis boundaries.

    Attributes:
        x: Looking at the cube along the x-axis, the basis of the walls observed.
        y: Looking at the cube along the y-axis, the basis of the walls observed.
        z: Looking at the cube along the z-axis, the basis of the walls observed.
    """

    x: ZXBasis
    y: ZXBasis
    z: ZXBasis

    def __post_init__(self) -> None:
        if self.x == self.y == self.z:
            raise TQECException(
                "The cube with the same basis along all axes is not allowed."
            )

    def as_tuple(self) -> tuple[ZXBasis, ZXBasis, ZXBasis]:
        """Return a tuple of ``(self.x, self.y, self.z)``.

        Returns:
            A tuple of ``(self.x, self.y, self.z)``.
        """
        return astuple(self)

    def __str__(self) -> str:
        return f"{self.x}{self.y}{self.z}"

    @staticmethod
    def all_kinds() -> list[ZXCube]:
        """Return all the allowed ``ZXCube`` instances.

        Returns:
            The list of all the allowed ``ZXCube`` instances.
        """
        return [ZXCube.from_str(s) for s in ["ZXZ", "XZZ", "ZXX", "XZX", "XXZ", "ZZX"]]

    @staticmethod
    def from_str(string: str) -> ZXCube:
        """Create a cube kind from the string representation.

        The string must be a 3-character string consisting of ``'X'`` or ``'Z'``,
        representing the basis of the walls along the x, y, and z axes.
        For example, a cube with left-right walls in the X basis, front-back walls in the Z basis,
        and top-bottom walls in the X basis can be constructed from the string ``'XZX'``.

        Args:
            string: A 3-character string consisting of ``'X'`` or ``'Z'``, representing
                the basis of the walls along the x, y, and z axes.

        Returns:
            The :py:class:`~tqec.computation.cube.ZXCube` instance constructed from
            the string representation.
        """
        return ZXCube(*map(ZXBasis, string.upper()))

    def to_zx_kind(self) -> ZXKind:
        if sum(basis == ZXBasis.Z for basis in astuple(self)) == 1:
            return ZXKind.Z
        return ZXKind.X

    @property
    def is_spatial_junction(self) -> bool:
        """Return whether a cube of this kind is a spatial junction.

        A spatial junction is a cube whose all spatial boundaries are in the same basis.
        And there are only two possible spatial junctions: ``XXZ`` and ``ZZX``.
        """
        return self.x == self.y

    def get_basis_along(self, direction: Direction3D) -> ZXBasis:
        """Get the basis of the walls along the given direction axis.

        Args:
            direction: The direction of the axis along which the basis is queried.

        Returns:
            The basis of the walls along the given direction axis.
        """
        return self.as_tuple()[direction.value]


class Port(CubeKind):
    """Cube kind representing the open ports in the block graph.

    The open ports correspond to the input/output of the computation
    represented by the block graph. They will have no effect on the
    functionality of the logical computation itself and should be
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
    """A fundamental building block of the logical computation.

    A cube is a high-level abstraction of a block of quantum operations within a
    specific spacetime volume. These operations preserve or manipulate the quantum
    information encoded in the logical qubits.

    For example, a single ``ZXZ`` kind cube can represent a quantum memory experiment for
    a surface code patch in logical Z basis. The default circuit implementation of the
    cube will consist of transversal Z basis resets, syndrome extraction cycles, and finally
    the Z basis transversal measurements. The spatial location of the physical qubits in the
    code patch and the time when the operations are applied are specified by the spacetime
    position of the cube.

    Attributes:
        position: The position of the cube in the spacetime. The spatial coordinates
            determines which code patch the operations are applied to, and the time
            coordinate determines when the operations are applied.
        kind: The kind of the cube. It determines the basic logical operations represented
            by the cube.
        label: The label of the cube. It's mainly used for annotating the input/output
            ports of the block graph. If the cube is a port, the label must be non-empty.
            Default is an empty string.
    """

    position: Position3D
    kind: CubeKind
    label: str = ""

    def __post_init__(self) -> None:
        if self.is_port and not self.label:
            raise TQECException("A port cube must have a non-empty port label.")

    def __str__(self) -> str:
        return f"{self.kind}{self.position}"

    @property
    def is_zx_cube(self) -> bool:
        """Return whether the cube is of kind
        :py:class:`~tqec.computation.cube.ZXCube`."""
        return isinstance(self.kind, ZXCube)

    @property
    def is_port(self) -> bool:
        """Return whether the cube is of kind
        :py:class:`~tqec.computation.cube.Port`."""
        return isinstance(self.kind, Port)

    @property
    def is_y_cube(self) -> bool:
        """Return whether the cube is of kind
        :py:class:`~tqec.computation.cube.YCube`."""
        return isinstance(self.kind, YCube)

    @property
    def is_spatial_junction(self) -> bool:
        """Return whether the cube is a spatial junction.

        A spatial junction is of kind :py:class:`~tqec.computation.cube.ZXCube` and its all
        spatial boundaries are in the same basis. There are only two possible spatial
        junctions: ``XXZ`` and ``ZZX``.
        """
        return isinstance(self.kind, ZXCube) and self.kind.is_spatial_junction

    def to_zx_node(self) -> ZXNode:
        """Convert the cube to a :py:class:`~tqec.computation.zx_graph.ZXNode`
        instance.

        Returns:
            A ZX node with the same position and label as the cube, and the kind of the
            node is converted from the cube kind with :py:meth:`~tqec.computation.cube.CubeKind.to_zx_kind`.
        """
        return ZXNode(self.position, self.kind.to_zx_kind(), self.label)
