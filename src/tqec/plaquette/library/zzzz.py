import cirq
from tqec.detectors.gate import DetectorGate, RelativeMeasurement
from tqec.plaquette.plaquette import PlaquetteList, SquarePlaquette
from tqec.plaquette.schedule import ScheduledCircuit
from tqec.position import Shape2D


class BaseZZZZPlaquette(SquarePlaquette):
    def __init__(self, circuit: ScheduledCircuit) -> None:
        super().__init__(
            circuit,
        )

    @property
    def shape(self) -> Shape2D:
        return Shape2D(3, 3)


class ZZZZSyndromeMeasurementPlaquette(BaseZZZZPlaquette):
    def __init__(
        self,
        schedule: list[int],
        detector: DetectorGate | None = None,
        reset_data_qubits: bool = False,
    ):
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        data_qubits = self.get_data_qubits_cirq()
        qubits_to_reset = [syndrome_qubit]
        if reset_data_qubits:
            qubits_to_reset += data_qubits
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        [
                            cirq.R(q).with_tags(self._MERGEABLE_TAG)
                            for q in qubits_to_reset
                        ],
                        [cirq.CX(data_qubits[0], syndrome_qubit)],
                        [cirq.CX(data_qubits[2], syndrome_qubit)],
                        [cirq.CX(data_qubits[1], syndrome_qubit)],
                        [cirq.CX(data_qubits[3], syndrome_qubit)],
                        [cirq.M(syndrome_qubit)],
                        detector.on(syndrome_qubit) if detector is not None else [],
                    ]
                ),
                schedule,
            ),
        )


class ZZZZInitialisationPlaquette(ZZZZSyndromeMeasurementPlaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
    ):
        detector = None
        if include_detector:
            detector = DetectorGate(
                [RelativeMeasurement(cirq.GridQubit(0, 0), -1)],
                time_coordinate=0,
            )
        super().__init__(schedule, detector, reset_data_qubits=True)


class ZZZZMemoryPlaquette(ZZZZSyndromeMeasurementPlaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
    ):
        detector = None
        if include_detector:
            detector = DetectorGate(
                [
                    RelativeMeasurement(cirq.GridQubit(0, 0), -1),
                    RelativeMeasurement(cirq.GridQubit(0, 0), -2),
                ],
                time_coordinate=0,
            )
        super().__init__(schedule, detector, reset_data_qubits=False)


class ZZZZFinalMeasurementPlaquette(BaseZZZZPlaquette):
    def __init__(
        self,
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = BaseZZZZPlaquette.get_syndrome_qubits_cirq()
        data_qubits = BaseZZZZPlaquette.get_data_qubits_cirq()
        detector = [
            cirq.Moment(
                DetectorGate(
                    [
                        RelativeMeasurement(cirq.GridQubit(0, 0), -1),
                        *[
                            RelativeMeasurement(dq - syndrome_qubit, -1)
                            for dq in data_qubits
                        ],
                    ],
                    qubit_coordinate_system_origin=syndrome_qubit,
                    time_coordinate=0,
                ).on(syndrome_qubit)
            )
        ]
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        cirq.Moment(
                            [
                                cirq.M(q).with_tags(self._MERGEABLE_TAG)
                                for q in data_qubits
                            ]
                        ),
                    ]
                    + (detector if include_detector else [])
                ),
            ),
        )


class ZZZZPlaquetteList(PlaquetteList):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
    ):
        super().__init__(
            [
                ZZZZInitialisationPlaquette(schedule, include_detector),
                ZZZZMemoryPlaquette(schedule),
                ZZZZFinalMeasurementPlaquette(include_detector),
            ]
        )
