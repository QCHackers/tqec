from __future__ import annotations

import cirq

from tqec.circuit.schedule import ScheduledCircuit
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    PlaquetteQubits,
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)


class ZInitialisationPlaquette(Plaquette):
    def __init__(self, qubits: PlaquetteQubits) -> None:
        circuit = cirq.Circuit(
            cirq.R(q).with_tags(self._MERGEABLE_TAG) for q in qubits.to_grid_qubit()
        )
        super().__init__(qubits, ScheduledCircuit(circuit))


class ZSquareInitialisationPlaquette(ZInitialisationPlaquette):
    def __init__(self) -> None:
        super().__init__(SquarePlaquetteQubits())


class ZRoundedInitialisationPlaquette(ZInitialisationPlaquette):
    def __init__(self, orientation: PlaquetteOrientation) -> None:
        super().__init__(RoundedPlaquetteQubits(orientation))


class XInitialisationPlaquette(Plaquette):
    def __init__(self, qubits: PlaquetteQubits) -> None:
        circuit = cirq.Circuit(
            (cirq.R(q).with_tags(self._MERGEABLE_TAG), cirq.H(q))
            for q in qubits.to_grid_qubit()
        )
        super().__init__(qubits, ScheduledCircuit(circuit))


class XSquareInitialisationPlaquette(XInitialisationPlaquette):
    def __init__(self) -> None:
        super().__init__(SquarePlaquetteQubits())


class XRoundedInitialisationPlaquette(XInitialisationPlaquette):
    def __init__(self, orientation: PlaquetteOrientation) -> None:
        super().__init__(RoundedPlaquetteQubits(orientation))
