import cirq

from tqec.circuit.operations.operation import make_detector
from tqec.circuit.schedule import ScheduledCircuit
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    PlaquetteQubits,
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)


class MeasurementPlaquette(Plaquette):
    def __init__(self, qubits: PlaquetteQubits, include_detector: bool = True):
        (syndrome_qubit,) = qubits.get_syndrome_qubits_cirq()
        data_qubits = qubits.get_data_qubits_cirq()
        measurement_qubits = [syndrome_qubit, *data_qubits]
        detector = make_detector(
            syndrome_qubit,
            [(meas_qubit - syndrome_qubit, -1) for meas_qubit in measurement_qubits],
        )
        super().__init__(
            qubits,
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


class MeasurementRoundedPlaquette(MeasurementPlaquette):
    def __init__(
        self, orientation: PlaquetteOrientation, include_detector: bool = True
    ):
        super().__init__(RoundedPlaquetteQubits(orientation), include_detector)


class MeasurementSquarePlaquette(MeasurementPlaquette):
    def __init__(self, include_detector: bool = True):
        super().__init__(SquarePlaquetteQubits(), include_detector)
