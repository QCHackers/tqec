from __future__ import annotations

from enum import Enum
from typing import Literal

import stim

from tqec.circuit.qubit import GridQubit
from tqec.circuit.schedule import Schedule, ScheduledCircuit
from tqec.exceptions import TQECException
from tqec.plaquette.enums import PlaquetteSide
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubits


class ResetBasis(Enum):
    X = "X"
    Z = "Z"

    @property
    def instruction_name(self) -> str:
        return f"R{self.value}"


class MeasurementBasis(Enum):
    X = "X"
    Z = "Z"

    @property
    def instruction_name(self) -> str:
        return f"M{self.value}"


def _make_pauli_syndrome_measurement_circuit(
    qubits: PlaquetteQubits,
    pauli_string: Literal["xx", "zz", "xxxx", "zzzz"],
    data_qubit_reset_basis: ResetBasis | None = None,
    data_qubit_measurement_basis: MeasurementBasis | None = None,
    plaquette_side: PlaquetteSide | None = None,
) -> stim.Circuit:
    """Build and return a quantum circuit measuring the provided Pauli
    syndrome.

    This function builds a quantum circuit measuring the Pauli observable
    provided in `pauli_string` on the provided `data_qubits`, using
    `syndrome_qubit` as an ancilla.

    Args:
        qubits: qubits on which the provided Pauli string will be measured.
            Includes the syndrome(s) qubit(s).
        pauli_string: a string representing the Pauli syndrome to measure. The
            string should have as many characters as there are qubits in
            `data_qubits`.
        data_qubit_reset_basis: if `None`, data qubits are not touched before
            measuring the provided Pauli operator. Else, data qubits are reset
            in the provided basis at the same time slice as the syndrome qubit
            (the first). Defaults to None.
        data_qubit_measurement_basis: if `None`, data qubits are not touched
            after measuring the provided Pauli operator. Else, data qubits are
            measured in the provided basis at the same time slice as the
            syndrome qubit (the last). Defaults to None.
        plaquette_side: if not `None`, data qubit reset/measurements are only
            added on the provided plaquette side. Else, they are added on all
            the qubits.

    Returns:
        a stim.Circuit instance measuring the provided Pauli string on the
        provided syndrome_qubit.

    Raises:
        TQECException: if `len(pauli_string) != len(data_qubits)`.
    """
    (sq,) = qubits.syndrome_qubits
    dqs = qubits.data_qubits
    if len(pauli_string) != len(dqs):
        raise TQECException(
            f"The number of Pauli characters provided ({len(pauli_string)}) "
            f"does not correspond to the number of data qubits ({len(dqs)})."
        )

    data_qubits_to_reset_measure: list[GridQubit] = dqs
    if plaquette_side is not None:
        data_qubits_to_reset_measure = qubits.get_qubits_on_side(plaquette_side)

    # Start the built quantum circuit by defining the correct qubit coordinates.
    circuit = stim.Circuit()
    q2i: dict[GridQubit, int] = {sq: 0} | {dq: i + 1 for i, dq in enumerate(dqs)}
    for qubit, qubit_index in q2i.items():
        circuit.append(qubit.to_qubit_coords_instruction(qubit_index))

    # Insert the appropriate reset gate (with a potential basis change for
    # syndrome qubit if needed).
    circuit.append("RX" if pauli_string in ["xx", "xxxx"] else "R", [q2i[sq]], [])
    if data_qubit_reset_basis is not None:
        circuit.append(
            data_qubit_reset_basis.instruction_name,
            [q2i[q] for q in data_qubits_to_reset_measure],
            [],
        )
    circuit.append("TICK", [], [])

    for i, pauli in enumerate(pauli_string.lower()):
        match pauli:
            case "z":
                circuit.append("CX", [q2i[dqs[i]], q2i[sq]], [])
            case "x":
                circuit.append("CX", [q2i[sq], q2i[dqs[i]]], [])
            case _:
                raise TQECException(f"Unsupported Pauli operation: {pauli}.")
        circuit.append("TICK", [], [])

    # Insert the appropriate measurement gate (with a potential basis change for
    # syndrome qubit if needed).
    circuit.append("MX" if pauli_string in ["xx", "xxxx"] else "M", [q2i[sq]], [])
    if data_qubit_measurement_basis is not None:
        circuit.append(
            data_qubit_measurement_basis.instruction_name,
            [q2i[q] for q in data_qubits_to_reset_measure],
            [],
        )

    return circuit


def pauli_memory_plaquette(
    qubits: PlaquetteQubits,
    pauli_string: Literal["xx", "zz", "xxxx", "zzzz"],
    schedule: Schedule,
    data_qubit_reset_basis: ResetBasis | None = None,
    data_qubit_measurement_basis: MeasurementBasis | None = None,
    plaquette_side: PlaquetteSide | None = None,
) -> Plaquette:
    """Generic function to create a :class:`Plaquette` instance measuring a
    given Pauli string.

    Args:
        qubits: qubits on which the provided Pauli string will be measured.
            Includes the syndrome(s) qubit(s).
        pauli_string: the Pauli string to measure on data qubit(s).
        schedule: scheduling of each time slice of the resulting circuit.
        data_qubit_reset_basis: if `None`, data qubits are not touched before
            measuring the provided Pauli operator. Else, data qubits are reset
            in the provided basis at the same time slice as the syndrome qubit
            (the first). Defaults to None.
        data_qubit_measurement_basis: if `None`, data qubits are not touched
            after measuring the provided Pauli operator. Else, data qubits are
            measured in the provided basis at the same time slice as the
            syndrome qubit (the last). Defaults to None.
        plaquette_side: if not `None`, data qubit reset/measurements are only
            added on the provided plaquette side. Else, they are added on all
            the qubits.
    Raises:
        TQECException: if the number of data qubits and the length of the
            provided Pauli string are not exactly equal.
        TQECException: if the provided schedule is incorrect.

    Returns:
        a `Plaquette` instance measuring the provided Pauli string.
    """
    circuit = _make_pauli_syndrome_measurement_circuit(
        qubits,
        pauli_string,
        data_qubit_reset_basis,
        data_qubit_measurement_basis,
        plaquette_side,
    )

    return Plaquette(qubits, ScheduledCircuit.from_circuit(circuit, schedule))
