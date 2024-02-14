import cirq
from tqec.detectors.operation import make_detector
from tqec.plaquette.plaquette import SquarePlaquette
from tqec.plaquette.schedule import ScheduledCircuit


class ZZZZSyndromeMeasurementPlaquette(SquarePlaquette):
    def __init__(
        self,
        schedule: list[int],
        qubits_to_reset: list[cirq.GridQubit],
        qubits_to_measure: list[cirq.GridQubit],
        detector: cirq.Operation | None = None,
    ) -> None:
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        data_qubits = self.get_data_qubits_cirq()
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        cirq.Moment(
                            cirq.R(q).with_tags(self._MERGEABLE_TAG)
                            for q in qubits_to_reset
                        ),
                        cirq.Moment(cirq.CX(data_qubits[0], syndrome_qubit)),
                        cirq.Moment(cirq.CX(data_qubits[2], syndrome_qubit)),
                        cirq.Moment(cirq.CX(data_qubits[1], syndrome_qubit)),
                        cirq.Moment(cirq.CX(data_qubits[3], syndrome_qubit)),
                        cirq.Moment(
                            cirq.M(q).with_tags(self._MERGEABLE_TAG)
                            for q in qubits_to_measure
                        ),
                        cirq.Moment(detector) if detector is not None else [],
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
        qubits_to_reset: list[cirq.GridQubit] | None = None,
    ):
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        data_qubits = self.get_data_qubits_cirq()
        detector = make_detector(
            syndrome_qubit,
            [(cirq.GridQubit(0, 0), -1)],
            time_coordinate=0,
        )
        if qubits_to_reset is None:
            qubits_to_reset = [syndrome_qubit, *data_qubits]

        super().__init__(
            schedule,
            qubits_to_reset=qubits_to_reset,
            qubits_to_measure=[syndrome_qubit],
            detector=detector if include_detector else None,
        )


class ZZZZMemoryPlaquette(ZZZZSyndromeMeasurementPlaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
        qubits_to_reset: list[cirq.GridQubit] | None = None,
    ):
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        detector = make_detector(
            syndrome_qubit,
            [(cirq.GridQubit(0, 0), -1), (cirq.GridQubit(0, 0), -2)],
            time_coordinate=0,
        )
        if qubits_to_reset is None:
            qubits_to_reset = [syndrome_qubit]

        super().__init__(
            schedule,
            qubits_to_reset=qubits_to_reset,
            qubits_to_measure=[syndrome_qubit],
            detector=detector if include_detector else None,
        )


class ZZZZFinalMeasurementPlaquette(SquarePlaquette):
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
        )
