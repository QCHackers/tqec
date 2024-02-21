import typing as ty

import cirq
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import RoundedPlaquette, SquarePlaquette
from tqec.plaquette.schedule import ScheduledCircuit


class ZSquareInitialisationPlaquette(SquarePlaquette):
    def __init__(
        self, qubits_to_initialise: ty.Sequence[cirq.GridQubit] | None = None
    ) -> None:
        if qubits_to_initialise is None:
            qubits_to_initialise = (
                SquarePlaquette.get_data_qubits_cirq()
                + SquarePlaquette.get_syndrome_qubits_cirq()
            )
        circuit = cirq.Circuit(
            cirq.R(q).with_tags(self._MERGEABLE_TAG) for q in qubits_to_initialise
        )
        super().__init__(ScheduledCircuit(circuit))


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
        circuit = cirq.Circuit(
            cirq.R(q).with_tags(self._MERGEABLE_TAG) for q in qubits_to_initialise
        )
        super().__init__(ScheduledCircuit(circuit), orientation)


class XSquareInitialisationPlaquette(SquarePlaquette):
    def __init__(
        self, qubits_to_initialise: ty.Sequence[cirq.GridQubit] | None = None
    ) -> None:
        if qubits_to_initialise is None:
            qubits_to_initialise = (
                SquarePlaquette.get_data_qubits_cirq()
                + SquarePlaquette.get_syndrome_qubits_cirq()
            )
        circuit = cirq.Circuit(
            (cirq.R(q).with_tags(self._MERGEABLE_TAG), cirq.H(q))
            for q in qubits_to_initialise
        )
        super().__init__(ScheduledCircuit(circuit))


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
        circuit = cirq.Circuit(
            (cirq.R(q).with_tags(self._MERGEABLE_TAG), cirq.H(q))
            for q in qubits_to_initialise
        )
        super().__init__(ScheduledCircuit(circuit), orientation)
