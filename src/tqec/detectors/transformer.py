from copy import deepcopy

import cirq
import numpy
import stimcirq
import sympy

from tqec.exceptions import TQECException
from tqec.detectors.operation import (
    ShiftCoords,
    Detector,
    Observable,
    STIM_TAG,
)
from tqec.detectors.measurement_map import CircuitMeasurementMap, compute_global_measurements_lookback_offsets


def _transform_to_stimcirq_compatible_impl(
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
                ) = _transform_to_stimcirq_compatible_impl(
                    operation.circuit.unfreeze(),
                    global_measurement_map=global_measurement_map,
                    current_moment_index_offset=current_moment_index,
                )
                number_of_moments_explored = (
                    index_of_last_explored_moment - current_moment_index
                ) * operation_repetitions
                operations.append(operation.replace(circuit=modified_circuit.freeze()))
                continue

            # All the stim-related annotations should have been tagged with STIM_TAG
            if STIM_TAG not in operation.tags:
                operations.append(deepcopy(operation))
                continue
            untagged = operation.untagged
            if isinstance(untagged, ShiftCoords):
                operations.append(stimcirq.ShiftCoordsAnnotation(untagged.shifts))
            elif isinstance(untagged, Detector):
                relative_keys = compute_global_measurements_lookback_offsets(
                    untagged, global_measurement_map, current_moment_index
                )
                detector_annotation = stimcirq.DetAnnotation(
                    relative_keys=relative_keys,
                    coordinate_metadata=untagged.coordinates,
                )
                operations.append(detector_annotation)
            elif isinstance(untagged, Observable):
                relative_keys = compute_global_measurements_lookback_offsets(
                    untagged, global_measurement_map, current_moment_index
                )
                observable_annotation = stimcirq.CumulativeObservableAnnotation(
                    relative_keys=relative_keys,
                    observable_index=untagged.index,
                )
                operations.append(observable_annotation)
            else:
                raise TQECException(
                    f"The operation {untagged} is tagged with {STIM_TAG} but is not an operation"
                    "recognized by tqec."
                )
        moments.append(cirq.Moment(*operations))
        current_moment_index += number_of_moments_explored

    return cirq.Circuit(moments), current_moment_index


@cirq.transformer
def transform_to_stimcirq_compatible(
    circuit: cirq.AbstractCircuit,
    *,
    context: cirq.TransformerContext | None = None,
) -> cirq.Circuit:
    """Transform the circuit to be compatible with stimcirq.

    stimcirq is a library that allows to convert cirq circuits to stim circuits. It defines a set of
    annotations in cirq that are used to represent the operations specific to stim. In tqec, we define
    the same annotations with different semantics. This transformer is used to convert the tqec
    annotations to the stimcirq annotations. The transformed operations are:

    - :class:`ShiftCoords`: converted to `stimcirq.ShiftCoordsAnnotation`.
    - :class:`Detector`: converted to `stimcirq.DetAnnotation` with the correct relative keys computed.
    - :class:`Observable`: converted to `stimcirq.CumulativeObservableAnnotation` with the correct
    relative keys computed.

    Args:
        circuit: The circuit to transform, which may contain tqec specific
            operations.
        context: See `cirq.transformer` documentation.

    Returns:
        A new circuit with the tqec specific operations transformed to stimcirq
        compatible operations.
    """
    _annotation_safety_check(circuit)
    measurement_map = CircuitMeasurementMap(circuit)
    transformed_circuit, _ = _transform_to_stimcirq_compatible_impl(circuit, measurement_map, 0)
    return transformed_circuit


def _annotation_safety_check(
    circuit: cirq.AbstractCircuit,
) -> None:
    """Check the first moment of the circuit for the presence of specific tqec annotations.

    The `Detector`/`Observable` annotations should not be present in the first moment of the circuit
    as there are no measurements to refer to. This function checks for the presence of these annotations
    and raises an exception if they are present.

    This exception is commonly raised when the user tries to append or insert a `Detector`/`Observable`
    operation directly to the circuit without a `cirq.Moment` around it.
    """
    first_moment = circuit.moments[0]
    for operation in first_moment.operations:
        if isinstance(operation.untagged, (Detector, Observable)):
            raise TQECException(
                f"The operation {operation.untagged} is a tqec specific operation that refers to a measurement"
                " but is present in the first moment of the circuit. This is not allowed as there are no"
                " measurements to refer to. This is likely due to the user trying to append or insert this"
                " operation directly to the circuit without a cirq.Moment around it."
            )
