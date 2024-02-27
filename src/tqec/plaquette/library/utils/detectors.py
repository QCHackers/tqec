import cirq
from tqec.detectors.operation import RelativeMeasurementData, make_detector
from tqec.plaquette.qubit import PlaquetteQubit


def make_memory_experiment_detector(
    syndrome_qubit: PlaquetteQubit,
    is_first_round: bool = False,
) -> cirq.Operation:
    detector_relative_measurements = [RelativeMeasurementData(cirq.GridQubit(0, 0), -1)]
    if not is_first_round:
        detector_relative_measurements.append(
            RelativeMeasurementData(cirq.GridQubit(0, 0), -2)
        )
    return make_detector(syndrome_qubit.to_grid_qubit(), detector_relative_measurements)
