from __future__ import annotations

from tqec.exceptions import TQECException
from tqec.plaquette.enums import PlaquetteOrientation

_QUBIT_INDICES = {
    PlaquetteOrientation.DOWN: (0, 1),
    PlaquetteOrientation.UP: (2, 3),
    PlaquetteOrientation.LEFT: (1, 3),
    PlaquetteOrientation.RIGHT: (0, 2),
}


def cnot_pauli_schedule(
    pauli_string: str,
    plaquette_orientation: PlaquetteOrientation,
    starting_index: int = 3,
) -> list[int]:
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
