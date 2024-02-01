import cirq
from tqec.detectors.gate import DetectorGate, RelativeMeasurement
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import PlaquetteList, RoundedPlaquette
from tqec.plaquette.schedule import ScheduledCircuit
from tqec.position import Shape2D


class BaseZZPlaquette(RoundedPlaquette):
    def __init__(
        self, circuit: ScheduledCircuit, orientation: PlaquetteOrientation
    ) -> None:
        super().__init__(circuit, orientation)

    @property
    def shape(self) -> Shape2D:
        # Hack to check the pre-condition that all Plaquette instances should
        # have the same shape.
        return Shape2D(3, 3)


class ZZSyndromeMeasurementPlaquette(BaseZZPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        detector: DetectorGate | None = None,
        reset_data_qubits: bool = False,
    ):
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        data_qubits = self.get_data_qubits_cirq(orientation)
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
                        [cirq.CX(data_qubits[1], syndrome_qubit)],
                        [cirq.M(syndrome_qubit)],
                        detector.on(syndrome_qubit) if detector is not None else [],
                    ]
                ),
                schedule,
            ),
            orientation=orientation,
        )


class ZZInitialisationPlaquette(ZZSyndromeMeasurementPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector: bool = True,
    ):
        detector = None
        if include_detector:
            detector = DetectorGate(
                [RelativeMeasurement(cirq.GridQubit(0, 0), -1)],
                time_coordinate=0,
            )
        super().__init__(orientation, schedule, detector, reset_data_qubits=True)


class ZZMemoryPlaquette(ZZSyndromeMeasurementPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
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
        super().__init__(orientation, schedule, detector, reset_data_qubits=False)


class ZZFinalMeasurementPlaquette(BaseZZPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        data_qubits = self.get_data_qubits_cirq(orientation)
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
                    time_coordinate=1,
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
            orientation=orientation,
        )


class ZZPlaquetteList(PlaquetteList):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector: bool = True,
    ):
        super().__init__(
            [
                ZZInitialisationPlaquette(orientation, schedule, include_detector),
                ZZMemoryPlaquette(orientation, schedule),
                ZZFinalMeasurementPlaquette(orientation, include_detector),
            ]
        )
