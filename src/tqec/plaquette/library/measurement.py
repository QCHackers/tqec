import cirq

from tqec.circuit.operations.operation import make_detector
from tqec.circuit.schedule import ScheduledCircuit
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import RoundedPlaquette, SquarePlaquette


class MeasurementRoundedPlaquette(RoundedPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = self.get_syndrome_qubits_cirq()
        data_qubits = self.get_data_qubits_cirq(orientation)
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
            orientation=orientation,
        )


class MeasurementSquarePlaquette(SquarePlaquette):
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
