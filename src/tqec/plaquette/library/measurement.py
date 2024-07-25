from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.pauli import pauli_memory_plaquette
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)


def xx_measurement_plaquette(
    orientation: PlaquetteOrientation,
    schedule: list[int],
) -> Plaquette:
    """R - H - CX - CX - H - M"""
    return pauli_memory_plaquette(
        RoundedPlaquetteQubits(orientation),
        "XX",
        schedule,
        include_final_data_measurements=True,
    )


def xxxx_measurement_plaquette(
    schedule: list[int],
) -> Plaquette:
    """R - H - CX - CX - CX - CX - H - M"""
    return pauli_memory_plaquette(
        SquarePlaquetteQubits(),
        "XXXX",
        schedule,
        include_final_data_measurements=True,
    )


def zz_measurement_plaquette(
    orientation: PlaquetteOrientation,
    schedule: list[int],
) -> Plaquette:
    """R - CX - CX - M"""
    return pauli_memory_plaquette(
        RoundedPlaquetteQubits(orientation),
        "ZZ",
        schedule,
        include_final_data_measurements=True,
    )


def zzzz_measurement_plaquette(
    schedule: list[int],
) -> Plaquette:
    """R - CX - CX - CX - CX - M"""
    return pauli_memory_plaquette(
        SquarePlaquetteQubits().permute_data_qubits([0, 2, 1, 3]),
        "ZZZZ",
        schedule,
        include_final_data_measurements=True,
    )
