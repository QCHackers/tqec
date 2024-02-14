import cirq
from tqec.enums import PlaquetteOrientation, PlaquetteSide
from tqec.exceptions import TQECException
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
            wrong_qubits = plaquette_qubits.difference(circuit_qubits)
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
    def qubits(self) -> list[PlaquetteQubit]:
        return self._qubits

    @property
    def circuit(self) -> ScheduledCircuit:
        return self._circuit


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

        Args:
            circuit: scheduled quantum circuit implementing the computation that
                the plaquette should represent.
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

    @staticmethod
    def get_qubits_on_side(side: PlaquetteSide) -> list[PlaquetteQubit]:
        data_indices: tuple[int, int]
        if side == PlaquetteSide.LEFT:
            data_indices = (0, 2)
        elif side == PlaquetteSide.RIGHT:
            data_indices = (1, 3)
        elif side == PlaquetteSide.UP:
            data_indices = (0, 1)
        else:  # if orientation == PlaquetteSide.DOWN:
            data_indices = (2, 3)
        return [SquarePlaquette._data_qubits[i] for i in data_indices]


class RoundedPlaquette(SquarePlaquette):
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
         /       \\
        | 1     2 |
        |---------|
        ```
        as `3` (the index of the bottom-right qubit in the initial ordering) is the
        lowest index (i.e., the number `1`) and `4` follows.

        Subclasses of this class should take that into account to apply operations
        on the correct qubits.
        This ordering is not to be confused with the temporal ordering of multi-qubit
        gates, for example in surface codes. It is a **qubit** ordering and has **no
        relation** with a temporal ordering.

        Args:
            circuit: scheduled quantum circuit implementing the computation that
                the plaquette should represent.
            orientation: side at which the plaquette is "pointing at". An
                orientation of PlaquetteOrientation.UP will generate a plaquette
                with its rounded side pointing up.
        """
        super().__init__(circuit)
        self._orientation = orientation

    @staticmethod
    def _get_data_qubit_side_from_plaquette_orientation(
        orientation: PlaquetteOrientation,
    ) -> PlaquetteSide:
        if orientation == PlaquetteOrientation.RIGHT:
            return PlaquetteSide.LEFT
        elif orientation == PlaquetteOrientation.LEFT:
            return PlaquetteSide.RIGHT
        elif orientation == PlaquetteOrientation.DOWN:
            return PlaquetteSide.UP
        else:  # if orientation == PlaquetteOrientation.UP:
            return PlaquetteSide.DOWN

    @staticmethod
    def get_data_qubits(orientation: PlaquetteOrientation) -> list[PlaquetteQubit]:
        """Returns the two data qubits of the plaquette

        This method returns the 2 data qubits according to the plaquette orientation. Taking
        the example from the class docstring, an orientation of PlaquetteOrientation.UP
        will return the qubits indexed 3 and 4 (or 2 and 3 in a 0-based indexing).

        Args:
            orientation: plaquette orientation
        """
        return RoundedPlaquette.get_qubits_on_side(
            RoundedPlaquette._get_data_qubit_side_from_plaquette_orientation(
                orientation
            )
        )

    @staticmethod
    def get_data_qubits_cirq(orientation: PlaquetteOrientation) -> list[cirq.GridQubit]:
        return [
            q.to_grid_qubit() for q in RoundedPlaquette.get_data_qubits(orientation)
        ]
