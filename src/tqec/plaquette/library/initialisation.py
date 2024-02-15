import typing as ty

import cirq
from tqec.enums import PlaquetteOrientation
from tqec.exceptions import TQECException
from tqec.plaquette.plaquette import RoundedPlaquette, SquarePlaquette
from tqec.plaquette.schedule import ScheduledCircuit


def _repeat_circuit_on_qubits(
    circuit: cirq.Circuit, qubits: ty.Sequence[cirq.GridQubit]
) -> cirq.Circuit:
    if len(circuit.all_qubits()) != 1:
        raise TQECException(
            "_repeat_circuit_on_qubits only accept 1-qubit circuits as input."
        )
    (raw_qubit,) = circuit.all_qubits()

    final_circuit = cirq.Circuit(
        [
            circuit.transform_qubits({raw_qubit: qubit}).all_operations()
            for qubit in qubits
        ],
    )
    return final_circuit


class ZSquareInitialisationPlaquette(SquarePlaquette):
    def __init__(
        self, qubits_to_initialise: ty.Sequence[cirq.GridQubit] | None = None
    ) -> None:
        if qubits_to_initialise is None:
            qubits_to_initialise = (
                SquarePlaquette.get_data_qubits_cirq()
                + SquarePlaquette.get_syndrome_qubits_cirq()
            )
        q = cirq.GridQubit(0, 0)
        circuit = cirq.Circuit(cirq.R(q))
        super().__init__(
            ScheduledCircuit(_repeat_circuit_on_qubits(circuit, qubits_to_initialise))
        )


class ZRoundedInitialisationPlaquette(RoundedPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        qubits_to_initialise: ty.Sequence[cirq.GridQubit] | None = None,
    ) -> None:
        if qubits_to_initialise is None:
            qubits_to_initialise = (
                RoundedPlaquette.get_data_qubits_cirq(orientation)
                + RoundedPlaquette.get_syndrome_qubits_cirq()
            )
        q = cirq.GridQubit(0, 0)
        circuit = cirq.Circuit(cirq.R(q))
        super().__init__(
            ScheduledCircuit(_repeat_circuit_on_qubits(circuit, qubits_to_initialise)),
            orientation,
        )


class XInitialisationPlaquette(SquarePlaquette):
    def __init__(
        self, qubits_to_initialise: ty.Sequence[cirq.GridQubit] | None = None
    ) -> None:
        if qubits_to_initialise is None:
            qubits_to_initialise = (
                SquarePlaquette.get_data_qubits_cirq()
                + SquarePlaquette.get_syndrome_qubits_cirq()
            )
        q = cirq.GridQubit(0, 0)
        circuit = cirq.Circuit(cirq.R(q), cirq.H(q))
        super().__init__(
            ScheduledCircuit(_repeat_circuit_on_qubits(circuit, qubits_to_initialise))
        )


class XRoundedInitialisationPlaquette(RoundedPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        qubits_to_initialise: ty.Sequence[cirq.GridQubit] | None = None,
    ) -> None:
        if qubits_to_initialise is None:
            qubits_to_initialise = (
                RoundedPlaquette.get_data_qubits_cirq(orientation)
                + RoundedPlaquette.get_syndrome_qubits_cirq()
            )
        q = cirq.GridQubit(0, 0)
        circuit = cirq.Circuit(cirq.R(q), cirq.H(q))
        super().__init__(
            ScheduledCircuit(_repeat_circuit_on_qubits(circuit, qubits_to_initialise)),
            orientation,
        )
