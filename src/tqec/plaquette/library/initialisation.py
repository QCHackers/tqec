from __future__ import annotations

from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.pauli import pauli_memory_plaquette
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)


def xx_initialisation_plaquette(
    orientation: PlaquetteOrientation,
    schedule: list[int],
) -> Plaquette:
    """R - H - CX - CX - H - M"""
    return pauli_memory_plaquette(
        RoundedPlaquetteQubits(orientation),
        "XX",
        schedule,
        include_initial_data_resets=True,
    )


def xxxx_initialisation_plaquette(
    schedule: list[int],
) -> Plaquette:
    """R - H - CX - CX - CX - CX - H - M"""
    return pauli_memory_plaquette(
        SquarePlaquetteQubits(),
        "XXXX",
        schedule,
        include_initial_data_resets=True,
    )


def zz_initialisation_plaquette(
    orientation: PlaquetteOrientation,
    schedule: list[int],
) -> Plaquette:
    """R - CX - CX - M"""
    return pauli_memory_plaquette(
        RoundedPlaquetteQubits(orientation),
        "ZZ",
        schedule,
        include_initial_data_resets=True,
    )


def zzzz_initialisation_plaquette(
    schedule: list[int],
) -> Plaquette:
    """R - CX - CX - CX - CX - M"""
    return pauli_memory_plaquette(
        SquarePlaquetteQubits().permute_data_qubits([0, 2, 1, 3]),
        "ZZZZ",
        schedule,
        include_initial_data_resets=True,
    )
