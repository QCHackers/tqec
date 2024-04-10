from __future__ import annotations

from tqec.plaquette.library.pauli import PauliMemoryPlaquette, pauli_memory_plaquette
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import SquarePlaquetteQubits


def zzzz_memory_plaquette(
    schedule: list[int],
    include_detector: bool = True,
    is_first_round: bool = False,
) -> Plaquette:
    return pauli_memory_plaquette(
        SquarePlaquetteQubits().permute_data_qubits([0, 2, 1, 3]),
        "ZZZZ",
        schedule,
        include_detector,
        is_first_round,
    )


class ZZZZMemoryPlaquette(PauliMemoryPlaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
        is_first_round: bool = False,
    ):
        super().__init__(
            SquarePlaquetteQubits().permute_data_qubits([0, 2, 1, 3]),
            "ZZZZ",
            schedule,
            include_detector,
            is_first_round,
        )
