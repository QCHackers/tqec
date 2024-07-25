from __future__ import annotations

from tqec.plaquette.library.pauli import pauli_memory_plaquette
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import SquarePlaquetteQubits


def xxxx_memory_plaquette(
    schedule: list[int],
    include_initial_resets: bool = False,
) -> Plaquette:
    return pauli_memory_plaquette(
        SquarePlaquetteQubits(),
        "XXXX",
        schedule,
        include_initial_resets,
    )
