from __future__ import annotations

import typing as ty

import stim

from tqec.exceptions import TQECException


class PauliString:
    def __init__(self, qubit2pauli: dict[int, str]):
        """A mapping from qubits to Pauli operators that represent a Pauli string.

        Args:
            qubits2pauli: A dictionary mapping qubit indices to Pauli operators. The
                Pauli operators should be one of "I", "X", "Y", or "Z".
        """
        for qubit, pauli in qubit2pauli.items():
            if pauli not in "IXYZ":
                raise TQECException(
                    f"Invalid Pauli operator {pauli} for qubit {qubit}, expected I, X, Y, or Z."
                )
        self.qubit2pauli = {q: qubit2pauli[q] for q in sorted(qubit2pauli.keys())}
        self._hash = hash(tuple(self.qubit2pauli.items()))

    @property
    def weight(self) -> int:
        return len([p for p in self.qubit2pauli.values() if p != "I"])

    @staticmethod
    def from_stim_pauli_string(
        stim_pauli_string: stim.PauliString,
        ignore_identity: bool = True,
    ) -> PauliString:
        """Convert a `stim.PauliString` to a `PauliString` instance, ignoring the sign."""
        if ignore_identity:
            return PauliString(
                {
                    q: "IXYZ"[stim_pauli_string[q]]
                    for q in range(len(stim_pauli_string))
                    if stim_pauli_string[q]
                }
            )
        return PauliString(
            {q: "IXYZ"[stim_pauli_string[q]] for q in range(len(stim_pauli_string))}
        )

    def to_stim_pauli_string(self, length: int | None) -> stim.PauliString:
        """Convert a `PauliString` to a `stim.PauliString` instance.

        Args:
            length: The length of the `stim.PauliString`. If `None`, the length is set to the
                maximum qubit index in the `PauliString` plus one.
        """
        max_qubit_index = max(self.qubit2pauli.keys())
        length = length or max_qubit_index + 1
        if length <= max_qubit_index:
            raise TQECException(
                f"The length specified {length} <= the maximum qubit index {max_qubit_index} in the pauli string."
            )
        stim_pauli_string = stim.PauliString(length)
        for q, p in self.qubit2pauli.items():
            stim_pauli_string[q] = p
        return stim_pauli_string

    def __bool__(self):
        return bool(self.qubit2pauli)

    def __mul__(self, other: PauliString) -> PauliString:
        result = {}
        for q in self.qubit2pauli.keys() | other.qubit2pauli.keys():
            a = self.qubit2pauli.get(q, "I")
            b = other.qubit2pauli.get(q, "I")
            ax = a in "XY"
            az = a in "YZ"
            bx = b in "XY"
            bz = b in "YZ"
            cx = ax ^ bx
            cz = az ^ bz
            c = "IXZY"[cx + cz * 2]
            result[q] = c
        return PauliString(result)

    def __repr__(self):
        return f"PauliString(qubits={self.qubit2pauli!r})"

    def __str__(self):
        return "*".join(
            f"{self.qubit2pauli[q]}{q}" for q in sorted(self.qubit2pauli.keys())
        )

    def __len__(self):
        return len(self.qubit2pauli)

    def commutes(self, other: PauliString) -> bool:
        """Check if this Pauli string commutes with another Pauli string."""
        return not self.anticommutes(other)

    def anticommutes(self, other: PauliString) -> bool:
        """Check if this Pauli string anticommutes with another Pauli string."""
        t = 0
        for q in self.qubit2pauli.keys() & other.qubit2pauli.keys():
            p1 = self.qubit2pauli[q]
            p2 = other.qubit2pauli[q]
            if p1 == "I" or p2 == "I":
                continue
            t += self.qubit2pauli[q] != other.qubit2pauli[q]
        return t % 2 == 1

    def collapse_by(self, collapse_operators: ty.Iterable[PauliString]):
        """Collapse the pauli string by the given operators.

        By collapsing, we mean that we replace the qubits that are in the given operators
        by identities.
        """
        pauli_string_copy = PauliString(self.qubit2pauli.copy())
        for operator in collapse_operators:
            for q in operator.qubit2pauli.keys():
                if q in pauli_string_copy.qubit2pauli:
                    pauli_string_copy.qubit2pauli[q] = "I"
        return pauli_string_copy

    def after(self, tableau: stim.Tableau, targets: ty.Iterable[int]) -> PauliString:
        stim_pauli_string = self.to_stim_pauli_string(
            length=max(list(targets) + list(self.qubit2pauli.keys())) + 1
        )
        stim_pauli_string_after = stim_pauli_string.after(tableau, targets=targets)
        return PauliString.from_stim_pauli_string(stim_pauli_string_after)

    def intersects(self, other: PauliString) -> bool:
        return bool(self.qubit2pauli.keys() & other.qubit2pauli.keys())

    def contains(self, other: PauliString) -> bool:
        return self.qubit2pauli.items() >= other.qubit2pauli.items()

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, PauliString):
            return NotImplemented
        return self.qubit2pauli == other.qubit2pauli


def _collapsing_inst_to_pauli_strings(
    inst: stim.CircuitInstruction,
) -> list[PauliString]:
    """Create the `PauliString` instances representing the provided collapsing instruction.

    Args:
        inst (stim.CircuitInstruction): a collapsing instruction.

    Raises:
        TQECException: If the provided collapsing instruction has any non-qubit target.
        TQECException: If the provided instruction is not a collapsing instruction.

    Returns:
        list[PauliString]: a list of `PauliString` instances representing the collapsing
            instruction provided as input.
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
    if name in ["MXX", "MYY", "MZZ"]:
        pauli = name[1]
        return [
            PauliString({t1.qubit_value: pauli, t2.qubit_value: pauli})  # type: ignore
            for t1, t2 in zip(targets[::2], targets[1::2])
        ]
    if name == "MPP":
        stim_pauli_strings = [
            stim.PauliString(pauli) for pauli in str(inst).split(" ")[1:]
        ]
        return [PauliString.from_stim_pauli_string(s) for s in stim_pauli_strings]
    raise TQECException(f"Not a collapsing instruction: {name}.")


def collapse_pauli_strings_at_moment(
    moment: stim.Circuit, is_reset: bool
) -> list[PauliString]:
    """Compute and return the list of PauliString instances representing all the
    collapsing operations found in the provided moment.

    This function has the following pre-condition: all the instructions in the provided
    moment should be instances of `stim.CircuitInstruction`.

    This pre-condition can be ensured by only providing `stim.Circuit` instances returned
    by the `iter_stim_circuit_by_moments` function, ensuring before calling that the
    moment is not an instance of `stim.CircuitRepeatBlock`.

    Args:
        moment (stim.Circuit): A circuit moment that does not contain any
            `stim.CircuitRepeatBlock` instance.
        is_reset (bool): If `True`, only return `PauliString` instances corresponding
            to reset collapsing operations. Else, only return `PauliString` instances
            corresponding to measurement collapsing operations.

    Raises:
        TQECException: If the pre-conditions of this function are not met.

    Returns:
        list[PauliString]: instances of `PauliString` representing each collapsing operation
            found in the provided moment, according to the provided value of `is_reset`.
    """
    # Pre-condition check
    if any(isinstance(inst, stim.CircuitRepeatBlock) for inst in moment):
        raise TQECException(
            "Pre-condition failed: collapse_pauli_strings_at_moment is expecting "
            "moments without repeat blocks."
        )

    def predicate(inst: stim.CircuitInstruction) -> bool:
        if is_reset:
            return stim.gate_data(inst.name).is_reset
        return stim.gate_data(inst.name).produces_measurements

    return [
        pauli_string
        for inst in moment
        if predicate(inst)  # type: ignore
        for pauli_string in _collapsing_inst_to_pauli_strings(inst)  # type: ignore
    ]
