from __future__ import annotations

from tqec.enums import PlaquetteOrientation
from tqec.plaquette.library.pauli import PauliMemoryPlaquette, pauli_memory_plaquette
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import RoundedPlaquetteQubits


def xx_memory_plaquette(
    orientation: PlaquetteOrientation,
    schedule: list[int],
    include_detector: bool = True,
    is_first_round: bool = False,
) -> Plaquette:
    return pauli_memory_plaquette(
        RoundedPlaquetteQubits(orientation),
        "XX",
        schedule,
        include_detector,
        is_first_round,
    )


class XXMemoryPlaquette(PauliMemoryPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector: bool = True,
        is_first_round: bool = False,
    ):
        super().__init__(
            RoundedPlaquetteQubits(orientation),
            "XX",
            schedule,
            include_detector,
            is_first_round,
        )
