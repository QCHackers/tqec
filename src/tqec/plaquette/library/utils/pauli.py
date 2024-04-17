from __future__ import annotations

import cirq
from tqec.exceptions import TQECException
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubit

_SUPPORTED_PAULI: set[str] = set("xz")


def make_pauli_syndrome_measurement_circuit(
    syndrome_qubit: PlaquetteQubit,
    data_qubits: list[PlaquetteQubit],
    pauli_string: str,
    reset_syndrome_qubit: bool = True,
) -> cirq.Circuit:
    """Build and return a quantum circuit measuring the provided Pauli syndrome.

    This function builds a quantum circuit measuring the Pauli observable
    provided in ``pauli_string`` on the provided ``data_qubits``, using
    ``syndrome_qubit`` as an ancilla.

    Args:
        syndrome_qubit: the ``PlaquetteQubit`` instance used to measure the
            syndrome. Will be reset at the beginning of the returned circuit
            if ``reset_syndrome_qubit`` is ``True``.
        data_qubits: the qubits we should measure the Pauli observable on.
            There should be as many ``PlaquetteQubit`` instances in
            ``data_qubits`` as there are Pauli characters in the provided
            ``pauli_string``.
        pauli_string: a string of case-independent characters, each
            representing a Pauli matrix. Each charater should be present in
            _SUPPORTED_PAULI and the string should have as many characters as
            there are qubits in ``data_qubits``.
        reset_syndrome_qubit: insert a reset gate on the syndrome qubit at the
            beginning of the circuit if True.

    Returns:
        a cirq.Circuit instance measuring the provided Pauli string on the
        provided syndrome_qubit.

    Raises:
        TQECException: if ``len(pauli_string) != len(data_qubits)`` or
            if ``any(p not in _SUPPORTED_PAULI for p in pauli_string)``.
    """
    if len(pauli_string) != len(data_qubits):
        raise TQECException(
            f"The number of Pauli characters provided ({len(pauli_string)}) "
            f"does not correspond to the number of data qubits ({len(data_qubits)})."
        )

    sq = syndrome_qubit.to_grid_qubit()
    dqs = [dq.to_grid_qubit() for dq in data_qubits]

    circuit = cirq.Circuit()
    if reset_syndrome_qubit:
        circuit.append(cirq.Moment(cirq.R(sq).with_tags(Plaquette._MERGEABLE_TAG)))

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
