from __future__ import annotations

from tqec.enums import PlaquetteOrientation
from tqec.plaquette.library.pauli import PauliMemoryPlaquette
from tqec.plaquette.qubit import RoundedPlaquetteQubits


class ZZMemoryPlaquette(PauliMemoryPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector: bool = True,
        is_first_round: bool = False,
    ):
        super().__init__(
            RoundedPlaquetteQubits(orientation),
            "ZZ",
            schedule,
            include_detector,
            is_first_round,
        )
