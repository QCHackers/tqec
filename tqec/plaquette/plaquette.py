import cirq

from tqec.enums import PlaquetteOrientation
from tqec.plaquette.qubit import PlaquetteQubit
from tqec.plaquette.schedule import ScheduledCircuit
from tqec.position import Position, Shape2D


class Plaquette:
    _MERGEABLE_TAG: str = "tqec_can_be_merged"

    @staticmethod
    def get_mergeable_tag() -> str:
        return Plaquette._MERGEABLE_TAG

    def __init__(self, qubits: list[PlaquetteQubit], circuit: ScheduledCircuit) -> None:
        """Represents a QEC plaquette"""
        self._qubits = qubits
        self._circuit = circuit

    @property
    def shape(self) -> Shape2D:
        maxx = max(qubit.position.x for qubit in self.qubits)
        maxy = max(qubit.position.y for qubit in self.qubits)
        return Shape2D(maxx + 1, maxy + 1)

    @property
    def qubits(self) -> list[PlaquetteQubit]:
        return self._qubits

    @property
    def circuit(self) -> ScheduledCircuit:
        return self._circuit


class SquarePlaquette(Plaquette):
    def __init__(self, circuit: ScheduledCircuit) -> None:
        super().__init__(self.get_data_qubits() + self.get_syndrome_qubits(), circuit)

    _data_qubits: list[PlaquetteQubit] = [
        PlaquetteQubit(Position(0, 0)),
        PlaquetteQubit(Position(2, 0)),
        PlaquetteQubit(Position(0, 2)),
        PlaquetteQubit(Position(2, 2)),
    ]
    _syndrome_qubits = [PlaquetteQubit(Position(1, 1))]

    @staticmethod
    def get_data_qubits() -> list[PlaquetteQubit]:
        return SquarePlaquette._data_qubits

    @staticmethod
    def get_syndrome_qubits() -> list[PlaquetteQubit]:
        return SquarePlaquette._syndrome_qubits

    @staticmethod
    def get_data_qubits_cirq() -> list[cirq.GridQubit]:
        return [q.to_grid_qubit() for q in SquarePlaquette.get_data_qubits()]

    @staticmethod
    def get_syndrome_qubits_cirq() -> list[cirq.GridQubit]:
        return [q.to_grid_qubit() for q in SquarePlaquette.get_syndrome_qubits()]


class RoundedPlaquette(Plaquette):
    def __init__(
        self, circuit: ScheduledCircuit, orientation: PlaquetteOrientation
    ) -> None:
        super().__init__(
            RoundedPlaquette.get_data_qubits(orientation)
            + RoundedPlaquette.get_syndrome_qubits(),
            circuit,
        )

    _data_qubits: list[PlaquetteQubit] = [
        PlaquetteQubit(Position(0, 0)),
        PlaquetteQubit(Position(2, 0)),
        PlaquetteQubit(Position(0, 2)),
        PlaquetteQubit(Position(2, 2)),
    ]
    _syndrome_qubits = [PlaquetteQubit(Position(1, 1))]

    @staticmethod
    def get_data_qubits(orientation: PlaquetteOrientation) -> list[PlaquetteQubit]:
        data_indices: tuple[int, int]
        if orientation == PlaquetteOrientation.RIGHT:
            data_indices = (0, 2)
        elif orientation == PlaquetteOrientation.LEFT:
            data_indices = (1, 3)
        elif orientation == PlaquetteOrientation.DOWN:
            data_indices = (0, 1)
        else:  # if orientation == PlaquetteOrientation.UP:
            data_indices = (2, 3)
        return [RoundedPlaquette._data_qubits[i] for i in data_indices]

    @staticmethod
    def get_syndrome_qubits() -> list[PlaquetteQubit]:
        return RoundedPlaquette._syndrome_qubits


class PlaquetteList:
    def __init__(self, plaquettes: list[Plaquette]) -> None:
        self._plaquettes = plaquettes

    @property
    def plaquettes(self) -> list[Plaquette]:
        return self._plaquettes
