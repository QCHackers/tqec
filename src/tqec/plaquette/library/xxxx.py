from __future__ import annotations

from tqec.plaquette.library.pauli import PauliMemoryPlaquette
from tqec.plaquette.qubit import SquarePlaquetteQubits


class XXXXMemoryPlaquette(PauliMemoryPlaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
        is_first_round: bool = False,
    ):
        super().__init__(
            SquarePlaquetteQubits(),
            "XXXX",
            schedule,
            include_detector,
            is_first_round,
        )
