from copy import deepcopy

import cirq
from tqec.detectors.gate import DetectorGate
from tqec.detectors.measurement_map import CircuitMeasurementMap


def _fill_in_detectors_global_record_indices_impl(
    circuit: cirq.AbstractCircuit,
    global_measurement_map: CircuitMeasurementMap,
    current_moment_index_offset: int,
) -> tuple[cirq.AbstractCircuit, int]:
    moments: list[cirq.Moment] = list()
    current_moment_index: int = current_moment_index_offset

    for moment in circuit.moments:
        operations: list[cirq.Operation] = list()
        number_of_moments_explored: int = 1
        for operation in moment.operations:
            if isinstance(operation, cirq.CircuitOperation):
                (
                    modified_circuit,
                    index_of_last_explored_moment,
                ) = _fill_in_detectors_global_record_indices_impl(
                    operation.circuit.unfreeze(),
                    global_measurement_map=global_measurement_map,
                    current_moment_index_offset=current_moment_index,
                )
                number_of_moments_explored = (
                    index_of_last_explored_moment - current_moment_index
                )
                operations.append(operation.replace(circuit=modified_circuit.freeze()))
            elif isinstance(operation.gate, DetectorGate):
                new_operation = deepcopy(operation)
                new_operation.gate: DetectorGate
                new_operation.gate.compute_global_measurements_loopback_offsets(
                    global_measurement_map, current_moment_index
                )
                operations.append(new_operation)
            else:
                operations.append(deepcopy(operation))
        moments.append(cirq.Moment(*operations))
        current_moment_index += number_of_moments_explored

    return cirq.Circuit(moments), current_moment_index


@cirq.transformer
def fill_in_detectors_global_record_indices(
    circuit: cirq.AbstractCircuit,
    *,
    context: cirq.TransformerContext | None = None,
    measurement_map: CircuitMeasurementMap | None = None,
) -> cirq.AbstractCircuit:
    """Compute and replace global measurement indices in detectors."""
    measurement_map = CircuitMeasurementMap(circuit)
    (
        filled_in_circuit,
        moment_number,
    ) = _fill_in_detectors_global_record_indices_impl(circuit, measurement_map, 0)
    return filled_in_circuit
