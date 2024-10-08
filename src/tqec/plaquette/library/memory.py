"""Defines regular plaquettes."""

from __future__ import annotations

from tqec.circuit.schedule import Schedule
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.pauli import pauli_memory_plaquette
from tqec.plaquette.library.utils.schedule import cnot_pauli_schedule
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import RoundedPlaquetteQubits, SquarePlaquetteQubits


def xx_memory_plaquette(
    orientation: PlaquetteOrientation, schedule: Schedule | None = None
) -> Plaquette:
    """RX - CX - CX - MX"""
    if schedule is None:
        schedule = Schedule.from_offsets(
            [0] + cnot_pauli_schedule("xx", orientation) + [5]
        )

    return pauli_memory_plaquette(RoundedPlaquetteQubits(orientation), "xx", schedule)


def xxxx_memory_plaquette(schedule: Schedule | None = None) -> Plaquette:
    """RX - CX - CX - CX - CX - MX"""
    if schedule is None:
        schedule = Schedule.from_offsets([0, 1, 2, 3, 4, 5])

    return pauli_memory_plaquette(SquarePlaquetteQubits(), "xxxx", schedule)


def zz_memory_plaquette(
    orientation: PlaquetteOrientation, schedule: Schedule | None = None
) -> Plaquette:
    """R - CX - CX - M"""
    if schedule is None:
        schedule = Schedule.from_offsets(
            [0] + cnot_pauli_schedule("zz", orientation) + [5]
        )

    return pauli_memory_plaquette(RoundedPlaquetteQubits(orientation), "zz", schedule)


def zzzz_memory_plaquette(schedule: Schedule | None = None) -> Plaquette:
    """R - CX - CX - CX - CX - M"""
    if schedule is None:
        schedule = Schedule.from_offsets([0, 1, 2, 3, 4, 5])

    return pauli_memory_plaquette(
        SquarePlaquetteQubits().permute_data_qubits([0, 2, 1, 3]), "zzzz", schedule
    )
