"""Introduces a convenience `PauliString` class.

This module implements an internal `PauliString` class with methods
that are used across the package. This class can easily be converted from
and to `stim.PauliString` and implement a subset of the `stim.PauliString`
API.
"""

from __future__ import annotations

import typing as ty

import stim
from attr import dataclass
from tqec.exceptions import TQECException


@dataclass(frozen=True)
class PauliString:
    """A mapping from qubits to Pauli operators that represent a Pauli string.

    Invariant:
        This class never stores identity Pauli terms. Any missing Pauli term is
        considered to be an identity.
        As such, it is illegal to initialise this class with an identity term.
    """

    pauli_by_qubit: dict[int, str]

    def __post_init__(self):
        for qubit, pauli in self.pauli_by_qubit.items():
            if pauli not in "XYZ":
                raise TQECException(
                    f"Invalid Pauli operator {pauli} for qubit {qubit}, expected X, Y, or Z."
                )

    @property
    def weight(self) -> int:
        return len(self.pauli_by_qubit)

    @staticmethod
    def from_stim_pauli_string(
        stim_pauli_string: stim.PauliString,
    ) -> PauliString:
        """Convert a `stim.PauliString` to a `PauliString` instance, ignoring the sign."""
        return PauliString(
            {
                q: "IXYZ"[stim_pauli_string[q]]
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
        max_qubit_index = max(self.pauli_by_qubit.keys())
        length = length or max_qubit_index + 1
        if length <= max_qubit_index:
            raise TQECException(
                f"The length specified {length} <= the maximum qubit index {max_qubit_index} in the pauli string."
            )
        stim_pauli_string = stim.PauliString(length)
        for q, p in self.pauli_by_qubit.items():
            stim_pauli_string[q] = p
        return stim_pauli_string

    def __bool__(self):
        return bool(self.pauli_by_qubit)

    def __mul__(self, other: PauliString) -> PauliString:
        result = {}
        for q in self.pauli_by_qubit.keys() | other.pauli_by_qubit.keys():
            a = self.pauli_by_qubit.get(q, "I")
            b = other.pauli_by_qubit.get(q, "I")
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
        return f"PauliString(qubits={self.pauli_by_qubit!r})"

    def __str__(self):
        return "*".join(
            f"{self.pauli_by_qubit[q]}{q}" for q in sorted(self.pauli_by_qubit.keys())
        )

    def __len__(self):
        return len(self.pauli_by_qubit)

    def commutes(self, other: PauliString) -> bool:
        """Check if this Pauli string commutes with another Pauli string."""
        return not self.anticommutes(other)

    def anticommutes(self, other: PauliString) -> bool:
        """Check if this Pauli string anticommutes with another Pauli string."""
        t = 0
        for q in self.pauli_by_qubit.keys() & other.pauli_by_qubit.keys():
            t += self.pauli_by_qubit[q] != other.pauli_by_qubit[q]
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
        ret = PauliString(self.pauli_by_qubit.copy())
        for operator in collapse_operators:
            if not ret.commutes(operator):
                raise TQECException(
                    f"Cannot collapse {ret} by a non-commuting operator {operator}."
                )
            ret *= operator
        return ret

    def after(self, tableau: stim.Tableau, targets: ty.Iterable[int]) -> PauliString:
        stim_pauli_string = self.to_stim_pauli_string(
            length=max(list(targets) + list(self.pauli_by_qubit.keys())) + 1
        )
        stim_pauli_string_after = stim_pauli_string.after(tableau, targets=targets)
        return PauliString.from_stim_pauli_string(stim_pauli_string_after)

    def intersects(self, other: PauliString) -> bool:
        return bool(self.pauli_by_qubit.keys() & other.pauli_by_qubit.keys())

    def contains(self, other: PauliString) -> bool:
        return self.pauli_by_qubit.items() >= other.pauli_by_qubit.items()

    def __eq__(self, other):
        """Check if two PauliString are equal.

        Args:
            other: the instance to compare to.

        Returns:
            `True` if the two `PauliString` instances are equal, else False.
        """
        if not isinstance(other, PauliString):
            return False
        return self.pauli_by_qubit == other.pauli_by_qubit


def _collapsing_inst_to_pauli_strings(
    inst: stim.CircuitInstruction,
) -> list[PauliString]:
    """Create the `PauliString` instances representing the provided collapsing instruction.

    Args:
        inst: a collapsing instruction.

    Raises:
        TQECException: If the provided collapsing instruction has any non-qubit target.
        TQECException: If the provided instruction is not a collapsing instruction.

    Returns:
        a list of `PauliString` instances representing the collapsing instruction
        provided as input.
    """
    name = inst.name
    targets = inst.targets_copy()
    if any(not t.is_qubit_target for t in targets):
        raise TQECException(
            "Found a stim instruction with non-qubit target. This is not supported."
        )
    if name in ["RX", "MX", "MRX"]:
        return [PauliString({target.qubit_value: "X"}) for target in targets]  # type: ignore
    if name in ["RY", "MY", "MRY"]:
        return [PauliString({target.qubit_value: "Y"}) for target in targets]  # type: ignore
    if name in ["R", "RZ", "M", "MZ", "MR", "MRZ"]:
        return [PauliString({target.qubit_value: "Z"}) for target in targets]  # type: ignore
    if name == "MPP":
        stim_pauli_strings = [
            stim.PauliString(pauli) for pauli in str(inst).split(" ")[1:]
        ]
        return [PauliString.from_stim_pauli_string(s) for s in stim_pauli_strings]
    raise TQECException(
        f"Not a collapsing instruction: {name}. "
        "See https://github.com/quantumlib/Stim/wiki/Stim-v1.13-Gate-Reference "
        "for a list of collapsing instructions."
    )


def collapse_pauli_strings_at_moment(moment: stim.Circuit) -> list[PauliString]:
    """Compute and return the list of PauliString instances representing all the
    collapsing operations found in the provided moment.

    This function has the following pre-condition: all the instructions in the provided
    moment should be instances of `stim.CircuitInstruction`.

    This pre-condition can be ensured by only providing `stim.Circuit` instances returned
    by the `iter_stim_circuit_by_moments` function, ensuring before calling that the
    moment is not an instance of `stim.CircuitRepeatBlock`.

    Args:
        moment: A circuit moment that does not contain any `stim.CircuitRepeatBlock`
            instance.

    Raises:
        TQECException: If the pre-conditions of this function are not met.

    Returns:
        list[PauliString]: instances of `PauliString` representing each collapsing operation
            found in the provided moment.
    """
    # Pre-condition check
    if any(isinstance(inst, stim.CircuitRepeatBlock) for inst in moment):
        raise TQECException(
            "Breaking pre-condition: collapse_pauli_strings_at_moment is expecting "
            f"moments without repeat blocks. Found:\n{moment}"
        )

    return [
        pauli_string
        for inst in moment
        for pauli_string in _collapsing_inst_to_pauli_strings(inst)  # type: ignore
    ]
