from __future__ import annotations

import typing as ty

import stim
from tqec.circuit.detectors.utils import (
    has_computation_instruction,
    has_measurement,
    has_reset,
    is_combined_measurement_reset,
    iter_stim_circuit_by_moments,
)


def _has_any_combined_gates(circuit: stim.Circuit) -> bool:
    for instruction in circuit:
        if isinstance(instruction, stim.CircuitRepeatBlock):
            if _has_any_combined_gates(instruction.body_copy()):
                return True
        elif is_combined_measurement_reset(instruction):
            return True
    return False


def does_not_contain_combined_gates(circuit: stim.Circuit) -> bool:
    return not _has_any_combined_gates(circuit)


def has_well_defined_moments(circuit: stim.Circuit) -> bool:
    for moment in iter_stim_circuit_by_moments(circuit):
        if isinstance(moment, stim.CircuitRepeatBlock):
            if not has_well_defined_moments(moment.body_copy()):
                return False
        else:
            measurement = has_measurement(moment)
            reset = has_reset(moment)
            computation = has_computation_instruction(moment)
            if measurement + reset + computation > 1:
                return False
    return True


def is_valid_input_circuit(circuit: stim.Circuit) -> str | None:
    predicates: list[tuple[ty.Callable[[stim.Circuit], bool], str]] = [
        (
            does_not_contain_combined_gates,
            "The provided quantum circuit should not contain any combined instruction (e.g., MR).",
        ),
        (
            has_well_defined_moments,
            "The provided quantum circuit contains at least one moment that has two different "
            "operation types from {reset, measurement, computation}.",
        ),
    ]

    for pred, reason in predicates:
        if not pred(circuit):
            return reason
    return None
