from __future__ import annotations

import typing
from enum import Enum

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
    syndrome_qubit_operation_name: typing.Literal["R", "M"],
    data_qubit_operation_basis: ResetBasis | MeasurementBasis | None = None,
    plaquette_side: PlaquetteSide | None = None,
    add_tick: bool = True,
) -> None:
    (syndrome_qubit,) = qubits.get_syndrome_qubits()
    data_qubits = qubits.get_data_qubits()

    # Apply the operation on the syndrome qubit
    circuit.append(syndrome_qubit_operation_name, [q2i[syndrome_qubit]], [])
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
    pauli_string: str,
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
        pauli_string: a string of case-independent characters, each
            representing a Pauli matrix. Each character should be either "x" or
            "z" (or their capitalized versions) and the string should have as
            many characters as there are qubits in `data_qubits`.
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
        TQECException: if `len(pauli_string) != len(data_qubits)` or
            if `any(p not in _SUPPORTED_PAULI for p in pauli_string)`.
    """
    (sq,) = qubits.get_syndrome_qubits()
    dqs = qubits.get_data_qubits()
    if len(pauli_string) != len(dqs):
        raise TQECException(
            f"The number of Pauli characters provided ({len(pauli_string)}) "
            f"does not correspond to the number of data qubits ({len(dqs)})."
        )

    # Start the built quantum circuit by defining the correct qubit coordinates.
    circuit = stim.Circuit()
    q2i: dict[GridQubit, int] = {sq: 0} | {dq: i + 1 for i, dq in enumerate(dqs)}
    for qubit, qubit_index in q2i.items():
        circuit.append(qubit.to_qubit_coords_instruction(qubit_index))

    _append_operation_inplace(
        circuit, qubits, q2i, "R", data_qubit_reset_basis, plaquette_side
    )

    is_in_X_basis: bool = False
    for i, pauli in enumerate(pauli_string.lower()):
        match pauli:
            case "z":
                if is_in_X_basis:
                    circuit.append("H", [q2i[sq]], [])
                    circuit.append("TICK", [], [])
                    is_in_X_basis = False
                circuit.append("CX", [q2i[dqs[i]], q2i[sq]], [])
                circuit.append("TICK", [], [])
            case "x":
                if not is_in_X_basis:
                    circuit.append("H", [q2i[sq]], [])
                    circuit.append("TICK", [], [])
                    is_in_X_basis = True
                circuit.append("CX", [q2i[sq], q2i[dqs[i]]], [])
                circuit.append("TICK", [], [])
            case _:
                raise TQECException(f"Unsupported Pauli operation: {pauli}.")

    if is_in_X_basis:
        circuit.append("H", [q2i[sq]], [])
        circuit.append("TICK", [], [])

    _append_operation_inplace(
        circuit,
        qubits,
        q2i,
        "M",
        data_qubit_measurement_basis,
        plaquette_side,
        add_tick=False,
    )
    return circuit


def pauli_memory_plaquette(
    qubits: PlaquetteQubits,
    pauli_string: str,
    schedule: Schedule,
    data_qubit_reset_basis: ResetBasis | None = None,
    data_qubit_measurement_basis: MeasurementBasis | None = None,
    plaquette_side: PlaquetteSide | None = None,
) -> Plaquette:
    """Generic function to create a :class:`Plaquette` instance measuring a
    given Pauli string.

    Warning:
        This function cannot change the order in which data qubits, Pauli
        "chars" (one character of the provided Pauli string) and schedule are
        provided. That means that it cannot group X and Z basis measurements.
        In practice, an input Pauli string "XZXZXZ" will lead to 3 pairs of
        Hadamard gates being included to measure the 3 X Pauli strings. The
        `schedule` provided by the user **have to take that into account** and
        schedule gates accordingly.

        For that reason, this function should be considered semi-public. You can
        use it, but take extra care if you do so.

        As a safeguard, this function will end up raising an error if the
        provided schedule is clearly incorrect (not in ascending order, missing
        entries, ...).

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
