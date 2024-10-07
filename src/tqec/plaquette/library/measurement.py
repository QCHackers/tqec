"""Defines regular plaquettes with measurements applied on data qubits."""

from __future__ import annotations

from tqec.circuit.schedule import Schedule
from tqec.plaquette.enums import PlaquetteOrientation, PlaquetteSide
from tqec.plaquette.library.pauli import MeasurementBasis, pauli_memory_plaquette
from tqec.plaquette.library.utils.schedule import cnot_pauli_schedule
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)


def xx_measurement_plaquette(
    orientation: PlaquetteOrientation,
    schedule: Schedule | None = None,
    data_qubit_measurement_basis: MeasurementBasis = MeasurementBasis.Z,
) -> Plaquette:
    """R - H - CX - CX - H - M"""
    if schedule is None:
        schedule = Schedule.from_offsets(
            [0, 1] + cnot_pauli_schedule("xx", orientation) + [6, 7]
        )

    return pauli_memory_plaquette(
        RoundedPlaquetteQubits(orientation),
        "XX",
        schedule,
        data_qubit_measurement_basis=data_qubit_measurement_basis,
    )


def xxxx_measurement_plaquette(
    schedule: Schedule | None = None,
    data_qubit_measurement_basis: MeasurementBasis = MeasurementBasis.Z,
    plaquette_side: PlaquetteSide | None = None,
) -> Plaquette:
    """R - H - CX - CX - CX - CX - H - M"""
    if schedule is None:
        schedule = Schedule.from_offsets([0, 1, 2, 3, 4, 5, 6, 7])

    return pauli_memory_plaquette(
        SquarePlaquetteQubits(),
        "XXXX",
        schedule,
        data_qubit_measurement_basis=data_qubit_measurement_basis,
        plaquette_side=plaquette_side,
    )


def zz_measurement_plaquette(
    orientation: PlaquetteOrientation,
    schedule: Schedule | None = None,
    data_qubit_measurement_basis: MeasurementBasis = MeasurementBasis.Z,
) -> Plaquette:
    """R - CX - CX - M"""
    if schedule is None:
        schedule = Schedule.from_offsets(
            [0] + cnot_pauli_schedule("zz", orientation) + [7]
        )

    return pauli_memory_plaquette(
        RoundedPlaquetteQubits(orientation),
        "ZZ",
        schedule,
        data_qubit_measurement_basis=data_qubit_measurement_basis,
    )


def zzzz_measurement_plaquette(
    schedule: Schedule | None = None,
    data_qubit_measurement_basis: MeasurementBasis = MeasurementBasis.Z,
    plaquette_side: PlaquetteSide | None = None,
) -> Plaquette:
    """R - CX - CX - CX - CX - M"""
    if schedule is None:
        schedule = Schedule.from_offsets([0, 2, 3, 4, 5, 7])

    return pauli_memory_plaquette(
        SquarePlaquetteQubits().permute_data_qubits([0, 2, 1, 3]),
        "ZZZZ",
        schedule,
        data_qubit_measurement_basis=data_qubit_measurement_basis,
        plaquette_side=plaquette_side,
    )
