from tqec.detectors.gate import DetectorGate
from tqec.enums import PlaquetteQubitType
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubit
from tqec.plaquette.schedule import ScheduledCircuit
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

    def _check_qubits(
        self, data_qubits: list[cirq.GridQubit], syndrome_qubits: list[cirq.GridQubit]
    ) -> None:
        assert (
            len(data_qubits) == 4
        ), f"Expected 4 data qubits, found {len(data_qubits)}: {data_qubits}"
        assert (
            len(syndrome_qubits) == 1
        ), f"Expected 1 syndrome qubit, found {len(syndrome_qubits)}: {syndrome_qubits}"

    def get_default_layers(
        self, data_qubits: list[cirq.GridQubit], syndrome_qubits: list[cirq.GridQubit]
    ) -> tuple[ScheduledCircuit, ScheduledCircuit, ScheduledCircuit]:
        self._check_qubits(data_qubits, syndrome_qubits)
        all_qubits = data_qubits + syndrome_qubits

        syndrome_qubit = syndrome_qubits[0]
        syndrome_operations: list[list[cirq.Operation]] = [
            [cirq.CX(data_qubits[0], syndrome_qubit)],
            [cirq.CX(data_qubits[1], syndrome_qubit)],
            [cirq.CX(data_qubits[2], syndrome_qubit)],
            [cirq.CX(data_qubits[3], syndrome_qubit)],
            [cirq.M(syndrome_qubit).with_tags(self._MERGEABLE_TAG)],
        ]
        return (
            # Initial layer, reset everything and perform one syndrome measurement.
            ScheduledCircuit(
                cirq.Circuit(
                    (
                        # Reset everything
                        [cirq.R(q).with_tags(self._MERGEABLE_TAG) for q in all_qubits],
                        *syndrome_operations,
                        [
                            DetectorGate(
                                syndrome_qubit,
                                [(syndrome_qubit, -1)],
                                time_coordinate=0,
                            ).on(syndrome_qubit)
                        ],
                    )
                ),
                self.get_cnot_schedule(),
            ),
            # Repeated layer, only reset syndrome qubits and perform one syndrome measurement.
            ScheduledCircuit(
                cirq.Circuit(
                    (
                        # Only reset syndrome qubit
                        [
                            cirq.R(sq).with_tags(self._MERGEABLE_TAG)
                            for sq in syndrome_qubits
                        ],
                        *syndrome_operations,
                        [
                            DetectorGate(
                                syndrome_qubit,
                                [(syndrome_qubit, -2), (syndrome_qubit, -1)],
                                time_coordinate=0,
                            ).on(syndrome_qubit)
                        ],
                    )
                ),
                self.get_cnot_schedule(),
            ),
            # Final layer, measure everything.
            ScheduledCircuit(
                cirq.Circuit(
                    (
                        # Only measure every qubit
                        [cirq.M(q).with_tags(self._MERGEABLE_TAG) for q in data_qubits],
                        [
                            DetectorGate(
                                syndrome_qubit,
                                [
                                    (syndrome_qubit, -1),
                                    *[(dq, -1) for dq in data_qubits],
                                ],
                                time_coordinate=1,
                            ).on(syndrome_qubit)
                        ],
                    )
                ),
            ),
        )
