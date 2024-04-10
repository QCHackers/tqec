from __future__ import annotations

from tqec.plaquette.library.pauli import pauli_memory_plaquette
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import SquarePlaquetteQubits


def xxxx_memory_plaquette(
    schedule: list[int],
    include_detector: bool = True,
    is_first_round: bool = False,
) -> Plaquette:
    return pauli_memory_plaquette(
        SquarePlaquetteQubits(),
        "XXXX",
        schedule,
        include_detector,
        is_first_round,
    )
