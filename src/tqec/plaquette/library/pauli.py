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


def _append_operation_inplace(
    circuit: stim.Circuit,
    qubits: PlaquetteQubits,
    q2i: dict[GridQubit, int],
    syndrome_qubit_operation_basis: ResetBasis | MeasurementBasis,
    data_qubit_operation_basis: ResetBasis | MeasurementBasis | None = None,
    plaquette_side: PlaquetteSide | None = None,
    add_tick: bool = True,
) -> None:
    (syndrome_qubit,) = qubits.syndrome_qubits
    data_qubits = qubits.data_qubits

    # Apply the operation on the syndrome qubit
    circuit.append(
        syndrome_qubit_operation_basis.instruction_name, [q2i[syndrome_qubit]], []
    )
    # Apply the operation on the data qubits in the appropriate basis if asked to
    if data_qubit_operation_basis is not None:
        qubits_to_apply_operation_to = data_qubits
        if plaquette_side is not None:
            qubits_to_apply_operation_to = qubits.get_qubits_on_side(plaquette_side)
        for data_qubit in qubits_to_apply_operation_to:
            circuit.append(
                data_qubit_operation_basis.instruction_name, [q2i[data_qubit]], []
            )
    if add_tick:
        circuit.append("TICK", [], [])


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
    syndrome_qubit_reset_basis: ResetBasis
    syndrome_qubit_measurement_basis: MeasurementBasis
    match pauli_string:
        case "xx" | "xxxx":
            syndrome_qubit_reset_basis = ResetBasis.X
            syndrome_qubit_measurement_basis = MeasurementBasis.X
        case "zz" | "zzzz":
            syndrome_qubit_reset_basis = ResetBasis.Z
            syndrome_qubit_measurement_basis = MeasurementBasis.Z

    # Start the built quantum circuit by defining the correct qubit coordinates.
    circuit = stim.Circuit()
    q2i: dict[GridQubit, int] = {sq: 0} | {dq: i + 1 for i, dq in enumerate(dqs)}
    for qubit, qubit_index in q2i.items():
        circuit.append(qubit.to_qubit_coords_instruction(qubit_index))

    _append_operation_inplace(
        circuit,
        qubits,
        q2i,
        syndrome_qubit_reset_basis,
        data_qubit_reset_basis,
        plaquette_side,
    )

    for i, pauli in enumerate(pauli_string.lower()):
        match pauli:
            case "z":
                circuit.append("CX", [q2i[dqs[i]], q2i[sq]], [])
                circuit.append("TICK", [], [])
            case "x":
                circuit.append("CX", [q2i[sq], q2i[dqs[i]]], [])
                circuit.append("TICK", [], [])
            case _:
                raise TQECException(f"Unsupported Pauli operation: {pauli}.")

    _append_operation_inplace(
        circuit,
        qubits,
        q2i,
        syndrome_qubit_measurement_basis,
        data_qubit_measurement_basis,
        plaquette_side,
        add_tick=False,
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
