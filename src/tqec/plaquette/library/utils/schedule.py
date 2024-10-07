"""Defines :func:`cnot_pauli_schedule` to abstract away some gate scheduling details.

Defining the right schedule for all the possible orientation of rounded
plaquettes (plaquettes at the side of logical qubits) is tedious to do by
hard-coding the schedules and easy to screw up when doing it generically.

This module takes the easy to screw up path and defines :func:`cnot_pauli_schedule`
that returns the schedule for 2-qubit gates in a rounded plaquette in a generic
manner. It has been checked several times, and should be correct.
"""

from __future__ import annotations

import typing

from tqec.exceptions import TQECException
from tqec.plaquette.enums import PlaquetteOrientation

_QUBIT_INDICES = {
    PlaquetteOrientation.DOWN: (0, 1),
    PlaquetteOrientation.UP: (2, 3),
    PlaquetteOrientation.LEFT: (1, 3),
    PlaquetteOrientation.RIGHT: (0, 2),
}


def cnot_pauli_schedule(
    pauli_string: typing.Literal["xx", "zz"],
    plaquette_orientation: PlaquetteOrientation,
    starting_index: int = 2,
) -> list[int]:
    """Return the schedule of the 2 CNOTs in the provided plaquette.

    Args:
        pauli_string: the type of Plaquette to schedule, that needs to be either
            "xx" or "zz".
        plaquette_orientation: orientation of the plaquette, used to compute
            which CNOT are used, and in consequence when they should be scheduled.
        starting_index: scheduling index at which the first CNOT can be executed.
            Defaults to 2 because 0 is associated to reset and 1 is associated to
            a potential Hadamard gate to measure X Pauli string stabilizers.

    Raises:
        TQECException: if the provided `pauli_string` is not "xx" nor "zz".

    Returns:
        a list of integers representing a partial schedule with two entries
        within `[starting_index, starting_index + 3]` representing the time at
        which the CNOTs implementing the plaquette should be scheduled.
    """
    if pauli_string not in {"xx", "zz"}:
        raise TQECException(
            f"No known default schedule for Pauli string {pauli_string}."
        )

    base_cnot_schedule = list(range(starting_index, starting_index + 4))
    if "z" in pauli_string:
        base_cnot_schedule[1], base_cnot_schedule[2] = (
            base_cnot_schedule[2],
            base_cnot_schedule[1],
        )

    return [base_cnot_schedule[i] for i in _QUBIT_INDICES[plaquette_orientation]]
