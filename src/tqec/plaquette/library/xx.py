from __future__ import annotations

from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.pauli import pauli_memory_plaquette
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import RoundedPlaquetteQubits


def xx_memory_plaquette(
    orientation: PlaquetteOrientation,
    schedule: list[int],
    include_initial_resets: bool = False,
) -> Plaquette:
    return pauli_memory_plaquette(
        RoundedPlaquetteQubits(orientation),
        "XX",
        schedule,
        include_initial_resets,
    )
