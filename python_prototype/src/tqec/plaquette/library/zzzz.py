from tqec.enums import PlaquetteQubitType
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubit
from tqec.position import Position

import cirq
from cirq.devices import GridQubit
from cirq.ops import Operation


class ZZZZPlaquette(Plaquette):
    def __init__(self):
        data_plaquette_qubits = [
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 0)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 2)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 0)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 2)),
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

    def get_cnot_schedule(self) -> list[int]:
        return [1, 2, 3, 4]

    def error_correction_round_with_measurement(
        self, data_qubits: list[GridQubit], syndrome_qubits: list[GridQubit]
    ) -> list[list[Operation]]:
        assert (
            len(data_qubits) == 4
        ), f"Expected 4 data qubits, found {len(data_qubits)}: {data_qubits}"
        assert (
            len(syndrome_qubits) == 1
        ), f"Expected 1 syndrome qubit, found {len(syndrome_qubits)}: {syndrome_qubits}"
        return [
            [cirq.CX(data_qubits[0], syndrome_qubits[0])],
            [cirq.CX(data_qubits[1], syndrome_qubits[0])],
            [cirq.CX(data_qubits[2], syndrome_qubits[0])],
            [cirq.CX(data_qubits[3], syndrome_qubits[0])],
            [cirq.M(syndrome_qubits[0], key="ZZZZ")],
        ]
