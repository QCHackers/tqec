from tqec.enums import PlaquetteQubitType, PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubit
from tqec.position import Position, Shape2D

import cirq


class ZZPlaquette(Plaquette):
    def __init__(self, orientation: PlaquetteOrientation):
        self._orientation = orientation
        _full_data_plaquette_qubits = [
            None,  # To have a 1-based indexing of this internal list.
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 0)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 2)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 0)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 2)),
        ]

        cnot_schedule = self.get_cnot_schedule()
        data_plaquette_qubits: list[PlaquetteQubit] = [
            _full_data_plaquette_qubits[i] for i in cnot_schedule
        ]
        syndrome_plaquette_qubit = PlaquetteQubit(
            PlaquetteQubitType.SYNDROME, Position(1, 1)
        )

        super().__init__(
            qubits=[*data_plaquette_qubits, syndrome_plaquette_qubit],
            layer_circuits=self.get_default_layers(
                [data_qubit.to_grid_qubit() for data_qubit in data_plaquette_qubits],
                [syndrome_plaquette_qubit.to_grid_qubit()],
            ),
        )

    def error_correction_round_with_measurement(
        self, data_qubits: list[cirq.GridQubit], syndrome_qubits: list[cirq.GridQubit]
    ) -> list[list[cirq.Operation]]:
        assert (
            len(data_qubits) == 2
        ), f"Expected 2 data qubits, found {len(data_qubits)}: {data_qubits}"
        assert (
            len(syndrome_qubits) == 1
        ), f"Expected 1 syndrome qubit, found {len(syndrome_qubits)}: {syndrome_qubits}"
        return [
            [cirq.CX(data_qubits[0], syndrome_qubits[0])],
            [cirq.CX(data_qubits[1], syndrome_qubits[0])],
            [cirq.M(syndrome_qubits[0], key="ZZ")],
        ]

    def get_cnot_schedule(self) -> list[int]:
        if self._orientation == PlaquetteOrientation.RIGHT:
            return [1, 2]
        elif self._orientation == PlaquetteOrientation.LEFT:
            return [3, 4]
        elif self._orientation == PlaquetteOrientation.DOWN:
            return [1, 3]
        else:  # if self._orientation == PlaquetteOrientation.UP:
            return [2, 4]

    @property
    def shape(self) -> Shape2D:
        return Shape2D(3, 3)
