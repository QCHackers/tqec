import cirq
from tqec.detectors.operation import make_detector
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import PlaquetteList, RoundedPlaquette
from tqec.plaquette.schedule import ScheduledCircuit
from tqec.position import Shape2D


class BaseXXPlaquette(RoundedPlaquette):
    def __init__(
        self,
        circuit: ScheduledCircuit,
        orientation: PlaquetteOrientation,
        add_unused_qubits: bool = False,
    ) -> None:
        super().__init__(circuit, orientation, add_unused_qubits)

    @property
    def shape(self) -> Shape2D:
        # Hack to check the pre-condition that all Plaquette instances should
        # have the same shape.
        return Shape2D(3, 3)


class XXSyndromeMeasurementPlaquette(BaseXXPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        detector: cirq.Operation | None = None,
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
                        cirq.Moment(
                            cirq.R(q).with_tags(self._MERGEABLE_TAG)
                            for q in qubits_to_reset
                        ),
                        cirq.Moment(cirq.H(syndrome_qubit)),
                        cirq.Moment(cirq.CX(syndrome_qubit, data_qubits[0])),
                        cirq.Moment(cirq.CX(syndrome_qubit, data_qubits[1])),
                        cirq.Moment(cirq.H(syndrome_qubit)),
                        cirq.Moment([cirq.M(syndrome_qubit)]),
                        cirq.Moment(detector) if detector is not None else [],
                    ]
                ),
                schedule,
            ),
            orientation=orientation,
        )


class XXInitialisationPlaquette(XXSyndromeMeasurementPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector: bool = True,
    ):
        detector = None
        if include_detector:
            (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
            detector = make_detector(
                syndrome_qubit,
                [(cirq.GridQubit(0, 0), -1)],
                time_coordinate=0,
            )
        super().__init__(orientation, schedule, detector, reset_data_qubits=True)


class XXMemoryPlaquette(XXSyndromeMeasurementPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
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
        super().__init__(orientation, schedule, detector, reset_data_qubits=False)


class XXFromXXXXPlaquette(XXSyndromeMeasurementPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector: bool = True,
    ):
        # Some qubits have just been measured. Get their offset to include them
        # in the detector.
        just_measured_qubits = self.get_unused_qubits_cirq(orientation)
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        measured_qubits_offsets = [q - syndrome_qubit for q in just_measured_qubits]

        # Regular detector offsets
        measurements_lookback_offsets = [
            (cirq.GridQubit(0, 0), -1),
            (cirq.GridQubit(0, 0), -2),
        ]
        # Adding the offset of the qubits we just measured.
        for offset in measured_qubits_offsets:
            measurements_lookback_offsets.append((offset, -1))

        detector = None
        if include_detector:
            (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
            detector = make_detector(
                syndrome_qubit,
                measurements_lookback_offsets,
                time_coordinate=0,
            )
        super().__init__(orientation, schedule, detector, reset_data_qubits=False)


class XXFinalMeasurementPlaquette(BaseXXPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        data_qubits = self.get_data_qubits_cirq(orientation)
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
            orientation=orientation,
        )


class XXPlaquetteList(PlaquetteList):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector: bool = True,
    ):
        super().__init__(
            [
                XXInitialisationPlaquette(orientation, schedule, include_detector),
                XXMemoryPlaquette(orientation, schedule),
                XXFinalMeasurementPlaquette(orientation, include_detector),
            ]
        )
