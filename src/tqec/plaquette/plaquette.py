import typing
from collections import defaultdict

from tqec.circuit.schedule import ScheduledCircuit
from tqec.exceptions import TQECException
from tqec.plaquette.qubit import PlaquetteQubits
from tqec.position import Position2D


class Plaquette:
    _MERGEABLE_TAG: str = "tqec_can_be_merged"

    @staticmethod
    def get_mergeable_tag() -> str:
        return Plaquette._MERGEABLE_TAG

    def __init__(
        self,
        name: str,
        qubits: PlaquetteQubits,
        circuit: ScheduledCircuit,
    ) -> None:
        """Represents a QEC plaquette

        This class stores qubits in the plaquette local coordinate system and a scheduled
        circuit that should be applied on those qubits to perform the QEC experiment.

        By convention, the local plaquette coordinate system is composed of a X-axis pointing
        to the right and a Y-axis pointing down.

        Args:
            name: name of the plaquette instance. Used to identify the plaquette (equality,
                hash, ...).
            qubits: qubits used by the plaquette circuit, given in the local
                plaquette coordinate system.
            circuit: scheduled quantum circuit implementing the computation that
                the plaquette should represent.

        Raises:
            TQECException: if the provided circuit uses qubits not in the list of
                PlaquetteQubit.
        """
        self._name = name
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
    def name(self) -> str:
        return self._name

    @property
    def origin(self) -> Position2D:
        return Position2D(0, 0)

    @property
    def qubits(self) -> PlaquetteQubits:
        return self._qubits

    @property
    def circuit(self) -> ScheduledCircuit:
        return self._circuit

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Plaquette) and self.name == value.name


Plaquettes = typing.Union[
    list[Plaquette], dict[int, Plaquette], defaultdict[int, Plaquette]
]
