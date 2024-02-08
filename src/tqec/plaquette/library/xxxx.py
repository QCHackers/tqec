import cirq
from tqec.detectors.operation import make_detector
from tqec.plaquette.plaquette import PlaquetteList, SquarePlaquette
from tqec.plaquette.schedule import ScheduledCircuit
from tqec.position import Shape2D


class BaseXXXXPlaquette(SquarePlaquette):
    def __init__(self, circuit: ScheduledCircuit) -> None:
        super().__init__(circuit)

    @property
    def shape(self) -> Shape2D:
        return Shape2D(3, 3)


class XXXXSyndromeMeasurementPlaquette(BaseXXXXPlaquette):
    def __init__(
        self,
        schedule: list[int],
        detector: cirq.Operation | None = None,
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
                        cirq.Moment(
                            cirq.R(q).with_tags(self._MERGEABLE_TAG)
                            for q in qubits_to_reset
                        ),
                        cirq.Moment(cirq.H(syndrome_qubit)),
                        cirq.Moment(cirq.CX(syndrome_qubit, data_qubits[0])),
                        cirq.Moment(cirq.CX(syndrome_qubit, data_qubits[1])),
                        cirq.Moment(cirq.CX(syndrome_qubit, data_qubits[2])),
                        cirq.Moment(cirq.CX(syndrome_qubit, data_qubits[3])),
                        cirq.Moment(cirq.H(syndrome_qubit)),
                        cirq.Moment(cirq.M(syndrome_qubit)),
                        cirq.Moment(detector) if detector is not None else [],
                    ]
                ),
                schedule,
            ),
        )


class XXXXInitialisationPlaquette(XXXXSyndromeMeasurementPlaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
    ):
        detector = None
        if include_detector:
            (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
            detector = make_detector(
                syndrome_qubit,
                [
                    (cirq.GridQubit(0, 0), -1),
                ],
                time_coordinate=0,
            )
        super().__init__(schedule, detector, reset_data_qubits=True)


class XXXXMemoryPlaquette(XXXXSyndromeMeasurementPlaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
    ):
        detector = None
        if include_detector:
            (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
            detector = make_detector(
                syndrome_qubit,
                [(cirq.GridQubit(0, 0), -1), (cirq.GridQubit(0, 0), -2)],
                time_coordinate=0,
            )
        super().__init__(schedule, detector, reset_data_qubits=False)


class XXXXFinalMeasurementPlaquette(BaseXXXXPlaquette):
    def __init__(
        self,
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        data_qubits = self.get_data_qubits_cirq()
        detector = make_detector(
            syndrome_qubit,
            [
                (cirq.GridQubit(0, 0), -1),
                *[(dq - syndrome_qubit, -1) for dq in data_qubits],
            ],
            time_coordinate=0,
        )
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
                        cirq.Moment(detector) if include_detector else [],
                    ]
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
