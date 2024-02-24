from __future__ import annotations

import cirq
from tqec.detectors.operation import RelativeMeasurementData, make_detector
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import RoundedPlaquette
from tqec.plaquette.schedule import ScheduledCircuit


class XXSyndromeMeasurementPlaquette(RoundedPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        detector: cirq.Operation | None = None,
    ) -> None:
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        data_qubits = self.get_data_qubits_cirq(orientation)
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        cirq.Moment(cirq.R(syndrome_qubit)),
                        cirq.Moment(cirq.H(syndrome_qubit)),
                        cirq.Moment(cirq.CX(syndrome_qubit, data_qubits[0])),
                        cirq.Moment(cirq.CX(syndrome_qubit, data_qubits[1])),
                        cirq.Moment(cirq.H(syndrome_qubit)),
                        cirq.Moment(cirq.M(syndrome_qubit)),
                        cirq.Moment(detector) if detector is not None else [],
                    ]
                ),
                schedule,
            ),
            orientation=orientation,
        )


class XXMemoryPlaquette(XXSyndromeMeasurementPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
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
            orientation,
            schedule,
            detector=detector if include_detector else None,
        )
