import cirq
from tqec.circuit.operations.operation import RelativeMeasurementData, make_detector
from tqec.plaquette.qubit import PlaquetteQubit


def make_memory_experiment_detector(
    syndrome_qubit: PlaquetteQubit,
    is_first_round: bool = False,
) -> cirq.Operation:
    """Build the Detector operation for a memory experiment

    Args:
        syndrome_qubit: the qubit used to non-destructively measure the syndrome.
        is_first_round: True if the detector is inserted on the first round of
            the memory experiment, i.e., if only one measurement already
            happened on the provided ``syndrome_qubit``.

    Returns:
        an instance of cirq.Operation representing a detector.
    """
    detector_relative_measurements = [RelativeMeasurementData(cirq.GridQubit(0, 0), -1)]
    if not is_first_round:
        detector_relative_measurements.append(
            RelativeMeasurementData(cirq.GridQubit(0, 0), -2)
        )
    return make_detector(syndrome_qubit.to_grid_qubit(), detector_relative_measurements)
