import cirq

from tqec.detectors.gate import DetectorGate, RelativeMeasurement
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubit
from tqec.plaquette.schedule import ScheduledCircuit
from tqec.position import Position, Shape2D


class ZZPlaquette(Plaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        include_initial_and_final_detectors: bool = True,
    ):
        self._orientation = orientation
        self._include_initial_and_final_detectors = include_initial_and_final_detectors
        _full_data_plaquette_qubits = [
            None,  # To have a 1-based indexing of this internal list.
            PlaquetteQubit(Position(0, 0)),
            PlaquetteQubit(Position(0, 2)),
            PlaquetteQubit(Position(2, 0)),
            PlaquetteQubit(Position(2, 2)),
        ]

        cnot_schedule = self.get_cnot_schedule()
        data_plaquette_qubits: list[PlaquetteQubit] = [
            _full_data_plaquette_qubits[i] for i in cnot_schedule
        ]
        syndrome_plaquette_qubit = PlaquetteQubit(Position(1, 1))

        super().__init__(
            qubits=[*data_plaquette_qubits, syndrome_plaquette_qubit],
            layer_circuits=self.get_default_layers(
                [data_qubit.to_grid_qubit() for data_qubit in data_plaquette_qubits],
                [syndrome_plaquette_qubit.to_grid_qubit()],
            ),
        )

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

    def _check_qubits(
        self, data_qubits: list[cirq.GridQubit], syndrome_qubits: list[cirq.GridQubit]
    ) -> None:
        assert (
            len(data_qubits) == 2
        ), f"Expected 2 data qubits, found {len(data_qubits)}: {data_qubits}"
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
            [cirq.M(syndrome_qubit).with_tags(self._MERGEABLE_TAG)],
        ]
        no_qubit_offset = cirq.GridQubit(0, 0)
        initial_detector = DetectorGate(
            syndrome_qubit,
            [RelativeMeasurement(no_qubit_offset, -1)],
            time_coordinate=0,
        ).on(syndrome_qubit)
        final_detector = DetectorGate(
            syndrome_qubit,
            [
                RelativeMeasurement(no_qubit_offset, -1),
                *[RelativeMeasurement(dq - syndrome_qubit, -1) for dq in data_qubits],
            ],
            time_coordinate=1,
        ).on(syndrome_qubit)
        return (
            # Initial layer, reset everything and perform one syndrome measurement.
            ScheduledCircuit(
                cirq.Circuit(
                    (
                        # Reset everything
                        [cirq.R(q).with_tags(self._MERGEABLE_TAG) for q in all_qubits],
                        *syndrome_operations,
                        [initial_detector]
                        if self._include_initial_and_final_detectors
                        else [],
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
                                [
                                    RelativeMeasurement(no_qubit_offset, -2),
                                    RelativeMeasurement(no_qubit_offset, -1),
                                ],
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
                        [final_detector]
                        if self._include_initial_and_final_detectors
                        else [],
                    )
                ),
            ),
        )
