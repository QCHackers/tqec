from __future__ import annotations

import cirq
from tqec.detectors.operation import RelativeMeasurementData, make_detector
from tqec.plaquette.plaquette import SquarePlaquette
from tqec.plaquette.schedule import ScheduledCircuit


class ZZZZSyndromeMeasurementPlaquette(SquarePlaquette):
    def __init__(
        self,
        schedule: list[int],
        detector: cirq.Operation | None = None,
    ) -> None:
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        data_qubits = self.get_data_qubits_cirq()
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        cirq.Moment(cirq.R(syndrome_qubit)),
                        cirq.Moment(cirq.CX(data_qubits[0], syndrome_qubit)),
                        cirq.Moment(cirq.CX(data_qubits[2], syndrome_qubit)),
                        cirq.Moment(cirq.CX(data_qubits[1], syndrome_qubit)),
                        cirq.Moment(cirq.CX(data_qubits[3], syndrome_qubit)),
                        cirq.Moment(cirq.M(syndrome_qubit)),
                        cirq.Moment(detector) if detector is not None else [],
                    ]
                ),
                schedule,
            ),
        )


class ZZZZMemoryPlaquette(ZZZZSyndromeMeasurementPlaquette):
    def __init__(
        self,
        schedule: list[int],
        include_detector: bool = True,
        is_first_round: bool = False,
    ):
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        detector_relative_measurements = [
            RelativeMeasurementData(cirq.GridQubit(0, 0), -1)
        ]
        if not is_first_round:
            detector_relative_measurements.append(
                RelativeMeasurementData(cirq.GridQubit(0, 0), -2)
            )
        detector = make_detector(syndrome_qubit, detector_relative_measurements)
        super().__init__(
            schedule,
            detector=detector if include_detector else None,
        )


class ZZZZFinalMeasurementPlaquette(SquarePlaquette):
    def __init__(
        self,
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        data_qubits = self.get_data_qubits_cirq()
        measurement_qubits = [syndrome_qubit, *data_qubits]
        detector = make_detector(
            syndrome_qubit,
            [(meas_qubit - syndrome_qubit, -1) for meas_qubit in measurement_qubits],
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
