import cirq

from tqec.detectors.gate import DetectorGate, RelativeMeasurement
from tqec.plaquette.plaquette import PlaquetteList, SquarePlaquette
from tqec.plaquette.schedule import ScheduledCircuit
from tqec.position import Shape2D


class BaseXXXXPlaquette(SquarePlaquette):
    def __init__(self, circuit: ScheduledCircuit) -> None:
        super().__init__(circuit)

    @property
    def shape(self) -> Shape2D:
        return Shape2D(3, 3)


class XXXXInitialisationPlaquette(BaseXXXXPlaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = BaseXXXXPlaquette.get_syndrome_qubits_cirq()
        data_qubits = BaseXXXXPlaquette.get_data_qubits_cirq()
        detector = []
        if include_detector:
            detector = [
                DetectorGate(
                    syndrome_qubit,
                    [RelativeMeasurement(cirq.GridQubit(0, 0), -1)],
                    time_coordinate=0,
                ).on(syndrome_qubit),
            ]
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        [
                            cirq.R(q).with_tags(self._MERGEABLE_TAG)
                            for q in [syndrome_qubit, *data_qubits]
                        ],
                        [cirq.H(syndrome_qubit)],
                        [cirq.CX(syndrome_qubit, data_qubits[0])],
                        [cirq.CX(syndrome_qubit, data_qubits[1])],
                        [cirq.CX(syndrome_qubit, data_qubits[2])],
                        [cirq.CX(syndrome_qubit, data_qubits[3])],
                        [cirq.H(syndrome_qubit)],
                        [cirq.M(syndrome_qubit)],
                        detector,
                    ]
                ),
                schedule,
            ),
        )


class XXXXMemoryPlaquette(BaseXXXXPlaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = BaseXXXXPlaquette.get_syndrome_qubits_cirq()
        data_qubits = BaseXXXXPlaquette.get_data_qubits_cirq()
        detector = [
            DetectorGate(
                syndrome_qubit,
                [
                    RelativeMeasurement(cirq.GridQubit(0, 0), -1),
                    RelativeMeasurement(cirq.GridQubit(0, 0), -2),
                ],
                time_coordinate=0,
            ).on(syndrome_qubit),
        ]
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        [
                            cirq.R(q).with_tags(self._MERGEABLE_TAG)
                            for q in [syndrome_qubit]
                        ],
                        [cirq.H(syndrome_qubit)],
                        [cirq.CX(syndrome_qubit, data_qubits[0])],
                        [cirq.CX(syndrome_qubit, data_qubits[1])],
                        [cirq.CX(syndrome_qubit, data_qubits[2])],
                        [cirq.CX(syndrome_qubit, data_qubits[3])],
                        [cirq.H(syndrome_qubit)],
                        [cirq.M(syndrome_qubit)],
                        detector,
                    ]
                ),
                schedule,
            ),
        )


class XXXXFinalMeasurementPlaquette(BaseXXXXPlaquette):
    def __init__(
        self,
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = BaseXXXXPlaquette.get_syndrome_qubits_cirq()
        data_qubits = BaseXXXXPlaquette.get_data_qubits_cirq()
        detector = [
            cirq.Moment(
                DetectorGate(
                    syndrome_qubit,
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
        )


class XXXXPlaquetteList(PlaquetteList):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
    ):
        super().__init__(
            [
                XXXXInitialisationPlaquette(schedule, include_detector),
                XXXXMemoryPlaquette(schedule),
                XXXXFinalMeasurementPlaquette(include_detector),
            ]
        )
