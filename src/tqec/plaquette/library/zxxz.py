"""Define the ZXXZ-type surface code plaquettes."""

from __future__ import annotations

from typing import Literal

import stim

from tqec.circuit.qubit_map import QubitMap
from tqec.circuit.schedule import ScheduledCircuit
from tqec.plaquette.enums import MeasurementBasis, ResetBasis
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import SquarePlaquetteQubits


def make_zxxz_surface_code_plaquette(
    basis: Literal["X", "Z"],
    data_qubits_initialization: ResetBasis | None = None,
    data_qubits_measurement: MeasurementBasis | None = None,
    x_boundary_orientation: Literal["HORIZONTAL", "VERTICAL"] = "VERTICAL",
) -> Plaquette:
    """Create a ZXXZ-type surface code plaquette. The circuit is adapted to
    superconducting qubits architecture s.t. all CNOTs are compiled to the
    CZ gates and additional Hadamard gates. Only Z basis reset and measurement
    are supported.

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
    qubits = SquarePlaquetteQubits()
    sq = 0
    # data qubits ordered as "Z" shape
    dqs = list(range(1, 5))
    i2q = QubitMap(
        {0: qubits.syndrome_qubits[0]}
        | {i + 1: q for i, q in enumerate(qubits.data_qubits)}
    )

    circuit = stim.Circuit()
    # 1. Initialization
    circuit.append("R", [sq], [])
    if data_qubits_initialization:
        circuit.append("R", dqs, [])
    circuit.append("TICK", [], [])
    circuit.append("H", [sq], [])
    if data_qubits_initialization:
        match basis, data_qubits_initialization:
            case ("Z", ResetBasis.Z) | ("X", ResetBasis.X):
                circuit.append("H", [dqs[1], dqs[2]], [])
            case _:
                circuit.append("H", [dqs[0], dqs[3]], [])
    circuit.append("TICK", [], [])

    # 2. CZ interactions
    # adjust cz order to make the hook errors perpendicular to the boundary
    match basis, x_boundary_orientation:
        case ("X", "HORIZONTAL") | ("Z", "VERTICAL"):
            cz_order = [1, 3, 2, 4]
        case _:
            cz_order = [1, 2, 3, 4]

    H_ON_ALL_DQS = "H " + " ".join(map(str, dqs))
    circuit += stim.Circuit(f"""
CZ {sq} {cz_order[0]}
TICK
{H_ON_ALL_DQS}
TICK
CZ {sq} {cz_order[1]}
TICK
CZ {sq} {cz_order[2]}
TICK
{H_ON_ALL_DQS}
TICK
CZ {sq} {cz_order[3]}
TICK
H {sq}
""")

    # 3. Measurement
    if data_qubits_measurement:
        match basis, data_qubits_measurement:
            case ("Z", MeasurementBasis.Z) | ("X", MeasurementBasis.X):
                circuit.append("H", [dqs[1], dqs[2]], [])
            case _:
                circuit.append("H", [dqs[0], dqs[3]], [])
    circuit.append("TICK", [], [])
    circuit.append("M", [sq], [])
    if data_qubits_measurement:
        circuit.append("M", dqs, [])

    return Plaquette(
        qubits,
        ScheduledCircuit.from_circuit(circuit, i2q=i2q),
        mergeable_instructions={"H", "R", "RZ", "M", "MZ"},
    )
