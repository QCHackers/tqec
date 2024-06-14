"""Introduces a convenience `PauliString` class.

This module implements an internal `PauliString` class with methods
that are used across the package. This class can easily be converted from
and to `stim.PauliString` and implement a subset of the `stim.PauliString`
API.
"""

from __future__ import annotations

import functools
import operator
import typing as ty

import stim
from tqec.exceptions import TQECException

_IXYZ: list[ty.Literal["I", "X", "Y", "Z"]] = ["I", "X", "Y", "Z"]


class PauliString:
    """A mapping from qubits to Pauli operators that represent a Pauli string.

    Invariant:
        This class never stores identity Pauli terms. Any missing Pauli term is
        considered to be an identity.
        As such, it is illegal to initialise this class with an identity term.
    """

    def __init__(
        self, pauli_by_qubit: dict[int, ty.Literal["I", "X", "Y", "Z"]]
    ) -> None:
        for qubit, pauli in pauli_by_qubit.items():
            if pauli not in "XYZ":
                raise TQECException(
                    f"Invalid Pauli operator {pauli} for qubit {qubit}, expected X, Y, or Z."
                )
        self._pauli_by_qubit = pauli_by_qubit
        self._hash = hash(tuple(self._pauli_by_qubit.items()))

    @property
    def weight(self) -> int:
        return len(self._pauli_by_qubit)

    @property
    def qubits(self) -> ty.Iterable[int]:
        return self._pauli_by_qubit.keys()

    @property
    def qubit(self) -> int:
        if len(self._pauli_by_qubit) != 1:
            raise TQECException(
                "Cannot retrieve only one qubit from a Pauli string with "
                f"{len(self._pauli_by_qubit)} qubits."
            )
        return next(iter(self.qubits))

    @staticmethod
    def from_stim_pauli_string(
        stim_pauli_string: stim.PauliString,
    ) -> PauliString:
        """Convert a `stim.PauliString` to a `PauliString` instance, ignoring the sign."""
        return PauliString(
            {
                q: _IXYZ[stim_pauli_string[q]]
                for q in range(len(stim_pauli_string))
                if stim_pauli_string[q]
            }
        )

    def to_stim_pauli_string(self, length: int | None) -> stim.PauliString:
        """Convert a `PauliString` to a `stim.PauliString` instance.

        Args:
            length: The length of the `stim.PauliString`. If `None`, the length is set to the
                maximum qubit index in the `PauliString` plus one.
        """
        max_qubit_index = max(self._pauli_by_qubit.keys())
        length = length or max_qubit_index + 1
        if length <= max_qubit_index:
            raise TQECException(
                f"The length specified {length} <= the maximum qubit index {max_qubit_index} in the pauli string."
            )
        stim_pauli_string = stim.PauliString(length)
        for q, p in self._pauli_by_qubit.items():
            stim_pauli_string[q] = p
        return stim_pauli_string

    def __bool__(self):
        return bool(self._pauli_by_qubit)

    def __mul__(self, other: PauliString) -> PauliString:
        result = {}
        for q in self._pauli_by_qubit.keys() | other._pauli_by_qubit.keys():
            a = self._pauli_by_qubit.get(q, "I")
            b = other._pauli_by_qubit.get(q, "I")
            ax = a in "XY"
            az = a in "YZ"
            bx = b in "XY"
            bz = b in "YZ"
            cx = ax ^ bx
            cz = az ^ bz
            c = "IXZY"[cx + cz * 2]
            if c != "I":
                result[q] = c
        return PauliString(result)

    def __repr__(self):
        return f"PauliString(qubits={self._pauli_by_qubit!r})"

    def __str__(self):
        return "*".join(
            f"{self._pauli_by_qubit[q]}{q}" for q in sorted(self._pauli_by_qubit.keys())
        )

    def __len__(self):
        return len(self._pauli_by_qubit)

    def commutes(self, other: PauliString) -> bool:
        """Check if this Pauli string commutes with another Pauli string."""
        return not self.anticommutes(other)

    def anticommutes(self, other: PauliString) -> bool:
        """Check if this Pauli string anticommutes with another Pauli string."""
        t = 0
        for q in self._pauli_by_qubit.keys() & other._pauli_by_qubit.keys():
            t += self._pauli_by_qubit[q] != other._pauli_by_qubit[q]
        return t % 2 == 1

    def collapse_by(self, collapse_operators: ty.Iterable[PauliString]):
        """Collapse the provided pauli string by the provided operators.

        Here, collapsing means that we are removing from the Pauli string represented
        by self all the commuting Pauli terms from all the provided operators.

        Args:
            collapse_operators: a collection of operators that should all commute
                with self and will collapse with self.

        Raises:
            TQECException: if one of the provided operators does not commute with self
                or if two of the provided operators are overlapping.

        Returns:
            a copy of self, collapsed by the provided operators.
        """
        ret = PauliString(self._pauli_by_qubit.copy())
        for op in collapse_operators:
            if not ret.commutes(op):
                raise TQECException(
                    f"Cannot collapse {ret} by a non-commuting operator {op}."
                )
            ret *= op
        return ret

    def after(self, tableau: stim.Tableau, targets: ty.Iterable[int]) -> PauliString:
        stim_pauli_string = self.to_stim_pauli_string(
            length=max(list(targets) + list(self._pauli_by_qubit.keys())) + 1
        )
        stim_pauli_string_after = stim_pauli_string.after(tableau, targets=targets)
        return PauliString.from_stim_pauli_string(stim_pauli_string_after)

    def intersects(self, other: PauliString) -> bool:
        return bool(self._pauli_by_qubit.keys() & other._pauli_by_qubit.keys())

    def contains(self, other: PauliString) -> bool:
        return self._pauli_by_qubit.items() >= other._pauli_by_qubit.items()

    def overlaps(self, other: PauliString) -> bool:
        return bool(self._pauli_by_qubit.keys() & other._pauli_by_qubit.keys())

    def __eq__(self, other):
        """Check if two PauliString are equal.

        Args:
            other: the instance to compare to.

        Returns:
            `True` if the two `PauliString` instances are equal, else False.
        """
        if not isinstance(other, PauliString):
            return False
        return self._pauli_by_qubit == other._pauli_by_qubit

    def __hash__(self) -> int:
        return self._hash

    def __getitem__(self, index: int) -> ty.Literal["I", "X", "Y", "Z"]:
        return self._pauli_by_qubit.get(index, "I")


def pauli_literal_to_bools(
    literal: ty.Literal["I", "X", "Y", "Z"],
) -> tuple[bool, bool]:
    if literal == "I":
        return (False, False)
    elif literal == "X":
        return (True, False)
    elif literal == "Y":
        return (True, True)
    elif literal == "Z":
        return (False, True)


def pauli_product(paulis: ty.Iterable[PauliString]) -> PauliString:
    return functools.reduce(operator.mul, paulis, PauliString({}))
