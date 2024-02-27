from __future__ import annotations

import cirq

from tqec.exceptions import TQECException
from tqec.plaquette.qubit import PlaquetteQubit

_SUPPORTED_PAULI: set[str] = set("xz")


def make_pauli_syndrome_measurement_circuit(
    syndrome_qubit: PlaquetteQubit,
    data_qubits: list[PlaquetteQubit],
    pauli_string: str,
    reset_syndrome_qubit: bool = True,
) -> cirq.Circuit:
    sq = syndrome_qubit.to_grid_qubit()
    dqs = [dq.to_grid_qubit() for dq in data_qubits]

    circuit = cirq.Circuit()
    if reset_syndrome_qubit:
        circuit.append(cirq.Moment(cirq.R(sq)))

    is_in_X_basis: bool = False
    for i, pauli in enumerate(pauli_string.lower()):
        if pauli not in _SUPPORTED_PAULI:
            raise TQECException(f"Unsupported Pauli operation: {pauli}.")
        if pauli == "z":
            if is_in_X_basis:
                circuit.append(cirq.Moment(cirq.H(sq)))
                is_in_X_basis = False
            circuit.append(cirq.Moment(cirq.CX(dqs[i], sq)))
        if pauli == "x":
            if not is_in_X_basis:
                circuit.append(cirq.Moment(cirq.H(sq)))
                is_in_X_basis = True
            circuit.append(cirq.Moment(cirq.CX(sq, dqs[i])))

    if is_in_X_basis:
        circuit.append(cirq.Moment(cirq.H(sq)))

    circuit.append(cirq.Moment(cirq.M(sq)))
    return circuit
