"""Define the standard CSS-type surface code plaquettes."""

from __future__ import annotations

from typing import Literal

import stim

from tqec.circuit.schedule import ScheduledCircuit
from tqec.plaquette.enums import MeasurementBasis, ResetBasis
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import SquarePlaquetteQubits


def make_css_surface_code_plaquette(
    basis: Literal["X", "Z"],
    data_qubits_initialization: ResetBasis | None = None,
    data_qubits_measurement: MeasurementBasis | None = None,
    x_boundary_orientation: Literal["HORIZONTAL", "VERTICAL"] = "HORIZONTAL",
) -> Plaquette:
    qubits = SquarePlaquetteQubits()
    sq = 0
    # data qubits ordered as "Z" shape
    dqs = range(1, 5)

    circuit = stim.Circuit()
    # 1. Initialization
    if data_qubits_initialization:
        circuit.append(data_qubits_initialization.instruction_name, dqs, [])
    circuit.append(f"R{basis}", [sq], [])
    circuit.append("TICK", [], [])

    # 2. CNOTs
    # adjust cnot order to make the hook errors perpendicular to the boundary
    match basis, x_boundary_orientation:
        case ("X", "HORIZONTAL") | ("Z", "VERTICAL"):
            cnot_order = [1, 3, 2, 4]
        case _:
            cnot_order = [1, 2, 3, 4]
    for dq in cnot_order:
        circuit.append("CX", [sq, dq][:: (-1 if basis == "Z" else 1)], [])
        circuit.append("TICK", [], [])

    # 3. Measurement
    if data_qubits_measurement:
        circuit.append(data_qubits_measurement.instruction_name, dqs, [])
    circuit.append(f"M{basis}", [sq], [])

    return Plaquette(qubits, ScheduledCircuit.from_circuit(circuit))
