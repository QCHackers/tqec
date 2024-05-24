from __future__ import annotations

from pydantic.dataclasses import dataclass

from tqec.circuit.schedule import ScheduledCircuit
from tqec.circuit.schemas import SupportedCircuitTypeEnum
from tqec.exceptions import TQECException
from tqec.plaquette.qubit import PlaquetteQubits
from tqec.plaquette.schemas import PlaquetteModel
from tqec.position import Position


class Plaquette:
    _MERGEABLE_TAG: str = "tqec_can_be_merged"

    @staticmethod
    def get_mergeable_tag() -> str:
        return Plaquette._MERGEABLE_TAG

    def __init__(
        self,
        qubits: PlaquetteQubits,
        circuit: ScheduledCircuit,
    ) -> None:
        """Represents a QEC plaquette

        This class stores qubits in the plaquette local coordinate system and a scheduled
        circuit that should be applied on those qubits to perform the QEC experiment.

        By convention, the local plaquette coordinate system is composed of a X-axis pointing
        to the right and a Y-axis pointing down.

        Args:
            qubits: qubits used by the plaquette circuit, given in the local
                plaquette coordinate system.
            circuit: scheduled quantum circuit implementing the computation that
                the plaquette should represent.

        Raises:
            TQECException: if the provided circuit uses qubits not in the list of
                PlaquetteQubit.
        """
        plaquette_qubits = {qubit.to_grid_qubit() for qubit in qubits}
        circuit_qubits = set(circuit.raw_circuit.all_qubits())
        if not circuit_qubits.issubset(plaquette_qubits):
            wrong_qubits = circuit_qubits.difference(plaquette_qubits)
            raise TQECException(
                f"The following qubits ({wrong_qubits}) are in the provided circuit "
                "but not in the list of PlaquetteQubit."
            )
        self._qubits = qubits
        self._circuit = circuit

    @property
    def origin(self) -> Position:
        return Position(0, 0)

    @property
    def qubits(self) -> PlaquetteQubits:
        return self._qubits

    @property
    def circuit(self) -> ScheduledCircuit:
        return self._circuit

    @staticmethod
    def from_model(model: PlaquetteModel) -> Plaquette:
        return Plaquette(model.qubits, ScheduledCircuit.from_model(model.circuit))

    def to_model(self, encoding: SupportedCircuitTypeEnum) -> PlaquetteModel:
        return PlaquetteModel(
            qubits=self.qubits, circuit=self.circuit.to_model(encoding)
        )


@dataclass
class PlaquetteLibrary:
    plaquettes: list[Plaquette]
