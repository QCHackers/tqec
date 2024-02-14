import cirq
from tqec.detectors.operation import make_detector
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import RoundedPlaquette
from tqec.plaquette.schedule import ScheduledCircuit


class ZZSyndromeMeasurementPlaquette(RoundedPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        qubits_to_reset: list[cirq.GridQubit],
        qubits_to_measure: list[cirq.GridQubit],
        detector: cirq.Operation | None = None,
    ) -> None:
        (syndrome_qubit,) = [q.to_grid_qubit() for q in self.get_syndrome_qubits()]
        data_qubits = [q.to_grid_qubit() for q in self.get_data_qubits(orientation)]
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        cirq.Moment(
                            cirq.R(q).with_tags(self._MERGEABLE_TAG)
                            for q in qubits_to_reset
                        ),
                        cirq.Moment(cirq.CX(data_qubits[0], syndrome_qubit)),
                        cirq.Moment(cirq.CX(data_qubits[1], syndrome_qubit)),
                        cirq.Moment(
                            cirq.M(q).with_tags(self._MERGEABLE_TAG)
                            for q in qubits_to_measure
                        ),
                        cirq.Moment(detector) if detector is not None else [],
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
        (syndrome_qubit,) = [q.to_grid_qubit() for q in self.get_syndrome_qubits()]
        data_qubits = [q.to_grid_qubit() for q in self.get_data_qubits(orientation)]
        detector = make_detector(
            syndrome_qubit,
            [(cirq.GridQubit(0, 0), -1)],
            time_coordinate=0,
        )

        super().__init__(
            orientation,
            schedule,
            qubits_to_reset=[syndrome_qubit, *data_qubits],
            qubits_to_measure=[syndrome_qubit],
            detector=detector if include_detector else None,
        )


class ZZMemoryPlaquette(ZZSyndromeMeasurementPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector=True,
    ):
        (syndrome_qubit,) = [q.to_grid_qubit() for q in self.get_syndrome_qubits()]
        detector = make_detector(
            syndrome_qubit,
            [(cirq.GridQubit(0, 0), -1), (cirq.GridQubit(0, 0), -2)],
            time_coordinate=0,
        )

        super().__init__(
            orientation,
            schedule,
            qubits_to_reset=[syndrome_qubit],
            qubits_to_measure=[syndrome_qubit],
            detector=detector if include_detector else None,
        )


class ZZFinalMeasurementPlaquette(RoundedPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = [q.to_grid_qubit() for q in self.get_syndrome_qubits()]
        data_qubits = [q.to_grid_qubit() for q in self.get_data_qubits(orientation)]
        detector = make_detector(
            syndrome_qubit,
            [
                (cirq.GridQubit(0, 0), -1),
                *[(dq - syndrome_qubit, -1) for dq in data_qubits],
            ],
            time_coordinate=1,
        )
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        cirq.Moment(
                            cirq.M(q).with_tags(self._MERGEABLE_TAG)
                            for q in data_qubits
                        ),
                        cirq.Moment(detector) if include_detector else [],
                    ]
                ),
            ),
            orientation=orientation,
        )
