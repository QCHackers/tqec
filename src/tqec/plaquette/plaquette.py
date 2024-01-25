import cirq

from tqec.enums import PlaquetteOrientation, PlaquetteOrigin
from tqec.plaquette.qubit import PlaquetteQubit
from tqec.plaquette.schedule import ScheduledCircuit
from tqec.position import Position


class Plaquette:
    _MERGEABLE_TAG: str = "tqec_can_be_merged"

    @staticmethod
    def get_mergeable_tag() -> str:
        return Plaquette._MERGEABLE_TAG

    def __init__(
        self,
        qubits: list[PlaquetteQubit],
        circuit: ScheduledCircuit,
        origin: PlaquetteOrigin = PlaquetteOrigin.BOTTOM_RIGHT,
        origin_index: int = 0,
    ) -> None:
        """Represents a QEC plaquette

        This class stores qubits in the plaquette local coordinate system and a scheduled
        circuit that should be applied on those qubits to perform the QEC experiment.

        By convention, the local plaquette coordinate system is composed of a X-axis pointing
        to the right and a Y-axis pointing down.

        :param qubits: qubits used by the plaquette circuit, given in the local plaquette
            coordinate system.
        :param circuit: scheduled quantum circuit implementing the computation that the
            plaquette should represent.
        :param origin: origin of the plaquette. This is used to compute the global position
            during the generation of the circuit.
        :param origin_index: index of the origin qubit in the list. Only used in combination
            with origin == PlaquetteOrigin.USER_DEFINED.

        :raises ValueError: if the number of qubits doesn't match the number of qubits
        """
        if len(qubits) != len(circuit.qubits):
            raise ValueError("Number of qubits doesn't match number of circuit qubits")

        self._qubits = qubits
        self._circuit = circuit
        self._caclulate_origin(origin, origin_index)

    @property
    def origin(self) -> Position:
        return self._origin

    @property
    def qubits(self) -> list[PlaquetteQubit]:
        return self._qubits

    @property
    def circuit(self) -> ScheduledCircuit:
        return self._circuit

    def _caclulate_origin(self, origin: PlaquetteOrigin, origin_index: int) -> None:
        """Calcluates the origin of the plaquette given the user input."""
        match origin:
            case PlaquetteOrigin.BOTTOM_RIGHT:
                max_x = max(qubit.position.x for qubit in self.qubits)
                max_y = max(qubit.position.y for qubit in self.qubits)
                self._origin = Position(max_x + 1, max_y + 1)
            case PlaquetteOrigin.CENTRAL:
                raise NotImplementedError()
            case PlaquetteOrigin.FIRST:
                self._origin = self._qubits[0].position
            case PlaquetteOrigin.USER_DEFINED:
                self._origin = self._qubits[origin_index].position


class SquarePlaquette(Plaquette):
    def __init__(self, circuit: ScheduledCircuit) -> None:
        """Represents a square QEC plaquette

        By convention, the qubits are sorted as depicted in the text below:
        ```text
        |---------|
        | 1     2 |
        |         |
        | 3     4 |
        |---------|
        ```
        Sub-classes of this class should take that into account to apply operations
        on the correct qubits.
        This ordering is not to be confused with the temporal ordering of multi-qubit
        gates, for example in surface codes. It is a **qubit** ordering and has **no
        relation** with a temporal ordering.

        :param circuit: scheduled quantum circuit implementing the computation that the
            plaquette should represent.
        """
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
        """Represents a rounded QEC plaquette

        By convention, the qubits are sorted as depicted in the text below:
        ```text
        |---------|
        | 1     2 |
        |         |
        | 3     4 |
        |---------|
        ```

        This means that an instance of a subclass of this class with a
        PlaquetteOrientation.UP orientation will have its two qubits ordered as
        ```text
          -------
         /       \
        | 1     2 |
        |---------|
        ```
        as `3` (the index of the bottom-right qubit in the initial ordering) is the 
        lowest index (i.e., the number `1`) and `4` follows.

        Sub-classes of this class should take that into account to apply operations
        on the correct qubits.
        This ordering is not to be confused with the temporal ordering of multi-qubit
        gates, for example in surface codes. It is a **qubit** ordering and has **no
        relation** with a temporal ordering.

        :param circuit: scheduled quantum circuit implementing the computation that the
            plaquette should represent.
        :param orientation: side at which the plaquette is "pointing at". An orientation
            of PlaquetteOrientation.UP will generate a plaquette with its rounded side
            pointing up.
        """
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
        """Returns the two data qubits of the plaquette

        This method returns the 2 data qubits according to the plaquette orientation. Taking
        the example from the class docstring, an orientation of PlaquetteOrientation.UP
        will return the qubits indexed 3 and 4 (or 2 and 3 in a 0-based indexing).

        :param orientation: plaquette orientation
        """
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
    """Basic wrapper over a list of Plaquette instances."""

    def __init__(self, plaquettes: list[Plaquette]) -> None:
        self._plaquettes = plaquettes

    @property
    def plaquettes(self) -> list[Plaquette]:
        return self._plaquettes
