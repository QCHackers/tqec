"""Defines :class:`GridQubit` and helper functions to manage qubits.

This module defines a central class to represent a qubit placed on a
2-dimensional grid, :class:`GridQubit`, and a few functions to extract
qubit-related information from `stim.Circuit` instances.
"""

from __future__ import annotations

import typing as ty
from collections import defaultdict
from fractions import Fraction

import stim

from tqec.position import Displacement, Position2D

NumericType = int | float | Fraction


def _to_fraction(value: NumericType) -> Fraction:
    if isinstance(value, int):
        return Fraction(value, 1)
    elif isinstance(value, float):
        return Fraction.from_float(value)
    return value


class GridQubit:
    """Represent a qubit placed on a 2-dimensional grid.

    Internally, this class represents the qubit coordinates as fractions. This
    design choice has been made for several reasons:

    - the :class:`fractions.Fraction` type is hashable (and its hash is usable,
      which is not the case for `float` for example).
    - most of the qubit coordinates we manipulated since the beginning are
      integers and so can be exactly represented by an instance of
      :class:`fractions.Fraction`.
    - it might make sense to have some qubits on "half-integer" (e.g., `0.5` or
      `4.5`) as some Crumble or Stim pre-built circuits use such coordinates.

    This means that the `x` and `y` coordinates will be returned as `Fraction`
    instances to the user.
    """

    def __init__(self, x: NumericType, y: NumericType) -> None:
        self._x = _to_fraction(x)
        self._y = _to_fraction(y)

    @property
    def x(self) -> Fraction:
        return self._x

    @property
    def y(self) -> Fraction:
        return self._y

    def to_qubit_coords_instruction(self, index: int) -> stim.CircuitInstruction:
        """Return the `QUBIT_COORDS` `stim.CircuitInstruction` needed to define
        `self` in a `stim.Circuit`."""
        # TODO: check ordering here.
        return stim.CircuitInstruction(
            "QUBIT_COORDS", [index], [float(self.x), float(self.y)]
        )

    def __add__(self, other: GridQubit | Position2D | Displacement) -> GridQubit:
        return GridQubit(self.x + other.x, self.y + other.y)

    def __sub__(self, other: GridQubit | Position2D | Displacement) -> GridQubit:
        return GridQubit(self.x - other.x, self.y - other.y)

    def __mul__(self, other: float) -> GridQubit:
        return GridQubit(other * self.x, other * self.y)

    def __rmul__(self, other: float) -> GridQubit:
        return GridQubit(other * self.x, other * self.y)

    def __hash__(self) -> int:
        return hash((self._x, self._y))

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, GridQubit) and self._x == value._x and self._y == value._y
        )

    def __lt__(self, other: GridQubit) -> bool:
        return (self._x, self._y) < (other._x, other._y)

    def __repr__(self) -> str:
        return f"GridQubit({self.x}, {self.y})"


"""Names of the `stim` instructions that are considered as annotations."""
ANNOTATION_INSTRUCTIONS: frozenset[str] = frozenset(
    [
        # Noise channels
        "CORRELATED_ERROR",
        "DEPOLARIZE1",
        "DEPOLARIZE2",
        "E",
        "ELSE_CORRELATED_ERROR",
        "HERALDED_ERASE",
        "HERALDED_PAULI_CHANNEL_1",
        "PAULI_CHANNEL_1",
        "PAULI_CHANNEL_2",
        "X_ERROR",
        "Y_ERROR",
        "Z_ERROR",
        # Annotations
        "DETECTOR",
        "MPAD",
        "OBSERVABLE_INCLUDE",
        "QUBIT_COORDS",
        "SHIFT_COORDS",
        "TICK",
    ]
)


def count_qubit_accesses(circuit: stim.Circuit) -> dict[int, int]:
    """Count the number of times a given qubit is used by an instruction that
    is not an annotation.

    Note:
        If a `REPEAT` instruction is found, each qubit access within the
        repeated block will be multiplied by the number of time the block is
        repeated.

    Args:
        circuit: circuit containing the gates.

    Returns:
        a mapping from qubit indices (as keys) to the number of non-annotation
        instructions that have this qubit index as target (as values).
    """
    counter: defaultdict[int, int] = defaultdict(int)
    for instruction in circuit:
        if isinstance(instruction, stim.CircuitRepeatBlock):
            for qi, count in count_qubit_accesses(instruction.body_copy()).items():
                counter[qi] += count * instruction.repeat_count
        else:
            if instruction.name in ANNOTATION_INSTRUCTIONS:
                continue
            for target in instruction.targets_copy():
                # Ignore targets that are not qubit targets.
                if not target.is_qubit_target:
                    continue
                qi = ty.cast(int, target.qubit_value)
                counter[qi] += 1
    return counter


def get_used_qubit_indices(circuit: stim.Circuit) -> frozenset[int]:
    """Returns the indices of qubits that are used by at least one non-
    annotation instruction.

    Args:
        circuit: circuit containing the gates.

    Returns:
        the set of qubit indices that are used by at least one non-annotation
        instruction.
    """
    return frozenset(count_qubit_accesses(circuit).keys())
