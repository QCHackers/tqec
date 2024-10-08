"""Define the standard CSS-type surface code plaquettes."""

from __future__ import annotations

from typing import Literal

import stim

from tqec.circuit.schedule import ScheduledCircuit
from tqec.exceptions import TQECException
from tqec.plaquette.enums import MeasurementBasis, ResetBasis
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import SquarePlaquetteQubits


def make_css_surface_code_plaquette(
    basis: Literal["X", "Z"] | str,
    data_qubits_initialization: ResetBasis | None = None,
    data_qubits_measurement: MeasurementBasis | None = None,
    x_boundary_orientation: Literal["HORIZONTAL", "VERTICAL"] = "VERTICAL",
) -> Plaquette:
    """Create a CSS-type surface code plaquette.

    Args:
        basis: The basis of the plaquette, either "X" or "Z".
        data_qubits_initialization: Initialization basis for the data qubits.
            If None, no initialization is performed.
        data_qubits_measurement: Measurement basis for the data qubits.
            If None, no measurement is performed.
        x_boundary_orientation: The orientation of the X boundary of the surface
            code block. Either "HORIZONTAL" or "VERTICAL". This determines the
            CNOT order in the plaquette together with the basis to prevent hook
            error from decreasing the code distance. Default is "HORIZONTAL".
    """
    if basis not in ["X", "Z"]:
        raise TQECException(f"Invalid basis: {basis}, only 'X' and 'Z' are allowed.")
    qubits = SquarePlaquetteQubits()
    sq = 0
    # data qubits ordered as "Z" shape
    dqs = range(1, 5)
    i2q = {0: qubits.syndrome_qubits[0]} | {
        i + 1: q for i, q in enumerate(qubits.data_qubits)
    }

    circuit = stim.Circuit()
    # 1. Initialization
    circuit.append(f"R{basis}", [sq], [])
    if data_qubits_initialization:
        circuit.append(data_qubits_initialization.instruction_name, dqs, [])
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
    circuit.append(f"M{basis}", [sq], [])
    if data_qubits_measurement:
        circuit.append(data_qubits_measurement.instruction_name, dqs, [])

    return Plaquette(qubits, ScheduledCircuit.from_circuit(circuit, i2q=i2q))
