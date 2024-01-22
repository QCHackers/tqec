from copy import deepcopy

import cirq
import numpy
import sympy

from tqec.detectors.gate import RelativeMeasurementGate
from tqec.detectors.measurement_map import CircuitMeasurementMap


def _fill_in_detectors_global_record_indices_impl(
    circuit: cirq.AbstractCircuit,
    global_measurement_map: CircuitMeasurementMap,
    current_moment_index_offset: int,
) -> tuple[cirq.Circuit, int]:
    moments: list[cirq.Moment] = list()
    current_moment_index: int = current_moment_index_offset

    for moment in circuit.moments:
        operations: list[cirq.Operation] = list()
        number_of_moments_explored: int = 1
        for operation in moment.operations:
            if isinstance(operation, cirq.CircuitOperation):
                # Getting the number of repetitions as an integer.
                operation_repetitions: int
                if isinstance(operation.repetitions, int):
                    operation_repetitions = operation.repetitions
                elif isinstance(operation.repetitions, sympy.Expr):
                    operation_repetitions = int(operation.repetitions.evalf())
                elif isinstance(operation.repetitions, numpy.integer):
                    operation_repetitions = int(operation.repetitions)
                else:
                    raise RuntimeError(
                        f"Wrong type for cirq.CircuitOperation.repetitions: {type(operation.repetitions).__str__}"
                    )
                # Recursively fill-in the detectors.
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
                ) * operation_repetitions
                operations.append(operation.replace(circuit=modified_circuit.freeze()))
            elif isinstance(operation.gate, RelativeMeasurementGate):
                assert len(operation.qubits) == 1, (
                    f"Cannot apply a {RelativeMeasurementGate.__class__.__name__} to more than "
                    f"1 qubits ({len(operation.qubits)} qubits given)."
                )
                new_operation = deepcopy(operation)
                relative_measurement_gate: RelativeMeasurementGate = new_operation.gate  # type: ignore
                relative_measurement_gate.compute_global_measurements_loopback_offsets(
                    global_measurement_map, current_moment_index
                )
                operations.append(new_operation)
            else:
                operations.append(deepcopy(operation))
        moments.append(cirq.Moment(*operations))
        current_moment_index += number_of_moments_explored

    return cirq.Circuit(moments), current_moment_index


@cirq.transformer
def fill_in_global_record_indices(
    circuit: cirq.AbstractCircuit,
    *,
    context: cirq.TransformerContext | None = None,
) -> cirq.Circuit:
    """Compute and replace global measurement indices in detectors

    This transformer iterates on all the operations contained in the provided cirq.AbstractCircuit
    instance and calls RelativeMeasurementGate._get_global_measurement_index and all the instances
    of RelativeMeasurementGate in order to replace their internal, local, measurement representation
    by the global records that will be useful to stim.

    :param circuit: instance containing the operations to fill-in with global measurement records
        understandable by stim.
    :param context: See cirq.transformer documentation.
    :returns: a copy of the given circuit with local measurement records replaced by global ones,
        understandable by stim.
    """
    measurement_map = CircuitMeasurementMap(circuit)
    (
        filled_in_circuit,
        _,
    ) = _fill_in_detectors_global_record_indices_impl(circuit, measurement_map, 0)
    return filled_in_circuit
