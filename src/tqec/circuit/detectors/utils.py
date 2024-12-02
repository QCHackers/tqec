from __future__ import annotations

import typing as ty

import numpy
import stim

from tqec.circuit.detectors.pauli import PauliString
from tqec.exceptions import TQECException

ANNOTATIONS = {
    "DETECTOR",
    "MPAD",
    "OBSERVABLE_INCLUDE",
    "QUBIT_COORDS",
    "SHIFT_COORDS",
    "TICK",
}


def iter_stim_circuit_by_moments(
    circuit: stim.Circuit,
) -> ty.Iterator[stim.Circuit | stim.CircuitRepeatBlock]:
    """Iterate over the `stim.Circuit` by moments.

    A moment in a `stim.Circuit` is a sequence of instructions between two `TICK`
    instructions. Note that we always consider a `stim.CircuitRepeatBlock` as a
    single moment.

    Args:
        circuit: The circuit to iterate over.

    Yields:
        A `stim.Circuit` or a `stim.CircuitRepeatBlock` instance.

    Invariants:
        - All the instructions of the provided circuit (even TICK ones) are
          eventually yielded by the generator returned by this function.
        - In the yield items, TICK instructions can only appear at the end of a `stim.Circuit`
          or within the body of a `stim.CircuitRepeatBlock`.
    """
    cur_moment = stim.Circuit()
    for inst in circuit:
        if isinstance(inst, stim.CircuitRepeatBlock):
            if cur_moment:
                yield cur_moment
                cur_moment.clear()
            yield inst
        elif inst.name == "TICK":
            cur_moment.append(inst)
            yield cur_moment
            cur_moment.clear()
        else:
            cur_moment.append(inst)
    if cur_moment:
        yield cur_moment


def is_measurement(instruction: stim.CircuitInstruction) -> bool:
    return instruction.name in ["M", "MR", "MRX", "MRY", "MRZ", "MX", "MY", "MZ"]


def is_reset(instruction: stim.CircuitInstruction) -> bool:
    return stim.gate_data(instruction.name).is_reset  # type: ignore


def is_noisy_gate(instruction: stim.CircuitInstruction) -> bool:
    return (
        not is_measurement(instruction)
        and stim.gate_data(instruction.name).is_noisy_gate
    )


def is_annotation(instruction: stim.CircuitInstruction) -> bool:
    return instruction.name in ANNOTATIONS


def is_virtual_instruction(inst: stim.CircuitInstruction) -> bool:
    return is_annotation(inst) or is_noisy_gate(inst)  # type: ignore


def is_combined_measurement_reset(instruction: stim.CircuitInstruction) -> bool:
    return is_measurement(instruction) and is_reset(instruction)


def has_combined_measurement_reset(moment: stim.Circuit) -> bool:
    """Check if a `stim.Circuit` moment contains combined instructions.

    Combined instructions are instructions that implement both a measurement and
    a reset in one step.

    Args:
        moment: The moment to check.

    Returns:
        `True` if the provided moment has a combined instruction, else `False`.
    """
    for inst in moment:
        if is_virtual_instruction(inst):  # type: ignore
            continue
        if is_combined_measurement_reset(inst):  # type: ignore
            return True
    return False


def has_circuit_repeat_block(moment: stim.Circuit) -> bool:
    """Check if a `stim.Circuit` moment contains a `stim.CircuitRepeatBlock`.

    Args:
        moment: The moment to check.

    Returns:
        `True` if the provided moment has a `stim.CircuitRepeatBlock`, else `False`.
    """
    return any(isinstance(inst, stim.CircuitRepeatBlock) for inst in moment)


def has_measurement(moment: stim.Circuit) -> bool:
    """Check if a `stim.Circuit` moment contains measurement instructions.

    Args:
        moment: The moment to check.

    Returns:
        `True` if the provided moment has a measurement, else `False`.
    """
    return any(is_measurement(inst) for inst in moment)  # type:ignore


def has_only_measurement_or_is_virtual(moment: stim.Circuit) -> bool:
    """Check if a `stim.Circuit` moment contains only measurement instructions
    or is a virtual moment.

    Note:
        Annotations are ignored by this function.

    Args:
        moment: The moment to check.

    Returns:
        `True` if the provided moment has a measurement, else `False`.
        Note that this function returns `True` on a moment that only contains
        annotations and noisy-gates (measurements excluded).
    """
    for inst in moment:
        if is_virtual_instruction(inst):  # type: ignore
            continue
        if not is_measurement(inst):  # type: ignore
            return False
    return True


def has_reset(moment: stim.Circuit) -> bool:
    """Check if a `stim.Circuit` moment contains reset instructions.

    Args:
        moment: The moment to check.

    Returns:
        `True` if the provided moment has a reset, else `False`.
    """
    return any(is_reset(inst) for inst in moment)  # type:ignore


def has_only_reset_or_is_virtual(moment: stim.Circuit) -> bool:
    """Check if a `stim.Circuit` moment contains only reset instructions or is
    a virtual moment.

    Note:
        Annotations are ignored by this function.

    Args:
        moment: The moment to check.

    Returns:
        `True` if the provided moment has only reset instructions, else `False`.
        Note that this function returns `True` on a moment that only contains
        annotations and noisy-gates (measurements excluded).
    """
    for inst in moment:
        if is_virtual_instruction(inst):  # type: ignore
            continue
        if not is_reset(inst):  # type: ignore
            return False
    return True


def is_virtual_moment(moment: stim.Circuit) -> bool:
    """Check if the provided moment only contains virtual instructions.

    Virtual instructions are noisy instructions or instructions whose name is
    in the `ANNOTATIONS` structure.

    Args:
        moment: circuit to check.

    Returns:
        `True` if the provided circuit is only composed of virtual instructions,
        else `False`.
    """
    if any(isinstance(inst, stim.CircuitRepeatBlock) for inst in moment):
        raise TQECException(
            "Breaking invariant: you provided a circuit with a stim.CircuitRepeatBlock "
            "instruction to is_virtual_moment. This is not supported."
        )
    return all(is_virtual_instruction(inst) for inst in moment)  # type:ignore


def has_computation_instruction(moment: stim.Circuit) -> bool:
    return any(
        not is_virtual_instruction(inst)  # type: ignore
        and not is_reset(inst)  # type: ignore
        and not is_measurement(inst)  # type: ignore
        for inst in moment
    )


def pauli_string_mean_coords(
    pauli_string: PauliString, qubit_coords_map: dict[int, list[float]]
) -> tuple[float, ...]:
    all_coords_items = [qubit_coords_map[i] for i in pauli_string.qubits]
    return tuple(numpy.mean(numpy.asarray(all_coords_items), axis=0)) + (0.0,)


def _collapsing_inst_to_pauli_strings(
    inst: stim.CircuitInstruction,
) -> list[PauliString]:
    """Create the `PauliString` instances representing the provided collapsing
    instruction.

    Args:
        inst: a collapsing instruction.

    Raises:
        TQECException: If the provided collapsing instruction has any non-qubit target.
        TQECException: If the provided instruction is not a collapsing instruction.

    Returns:
        a list of `PauliString` instances representing the collapsing instruction
        provided as input.
    """
    name = inst.name
    targets = inst.targets_copy()
    if any(not t.is_qubit_target for t in targets):
        raise TQECException(
            "Found a stim instruction with non-qubit target. This is not supported."
        )
    if name in ["RX", "MX", "MRX"]:
        return [PauliString({target.qubit_value: "X"}) for target in targets]  # type: ignore
    if name in ["RY", "MY", "MRY"]:
        return [PauliString({target.qubit_value: "Y"}) for target in targets]  # type: ignore
    if name in ["R", "RZ", "M", "MZ", "MR", "MRZ"]:
        return [PauliString({target.qubit_value: "Z"}) for target in targets]  # type: ignore
    raise TQECException(
        f"Not a supported collapsing instruction: {name}. "
        "See https://github.com/quantumlib/Stim/wiki/Stim-v1.13-Gate-Reference "
        "for a list of collapsing instructions."
    )


def collapse_pauli_strings_at_moment(moment: stim.Circuit) -> list[PauliString]:
    """Compute and return the list of PauliString instances representing all
    the collapsing operations found in the provided moment.

    This function has the following pre-condition: all the instructions in the provided
    moment should be instances of `stim.CircuitInstruction`.

    This pre-condition can be ensured by only providing `stim.Circuit` instances returned
    by the `iter_stim_circuit_by_moments` function, ensuring before calling that the
    moment is not an instance of `stim.CircuitRepeatBlock`.

    This function ensures that the returned Pauli strings are ordered w.r.t the
    qubit index the collapsing operation was applied on.

    Args:
        moment: A circuit moment that does not contain any `stim.CircuitRepeatBlock`
            instance.

    Raises:
        TQECException: If the pre-conditions of this function are not met.

    Returns:
        instances of `PauliString` representing each collapsing operation found in the
            provided moment, sorted by qubits.
    """
    # Pre-condition check
    if any(isinstance(inst, stim.CircuitRepeatBlock) for inst in moment):
        raise TQECException(
            "Breaking pre-condition: collapse_pauli_strings_at_moment is expecting "
            f"moments without repeat blocks. Found:\n{moment}"
        )

    pauli_strings: list[PauliString] = []
    for inst in moment:
        if is_virtual_instruction(inst):  # type: ignore
            continue
        collapsing_operations = _collapsing_inst_to_pauli_strings(inst)  # type: ignore
        pauli_strings.extend(collapsing_operations)
    return pauli_strings


def remove_annotations(
    circuit: stim.Circuit,
    annotations_to_remove: frozenset[str] = frozenset(
        {"DETECTOR", "MPAD", "OBSERVABLE_INCLUDE", "SHIFT_COORDS"}
    ),
) -> stim.Circuit:
    """Remove all the annotations from a given circuit, except TICK
    instructions.

    Args:
        circuit: the circuit to remove annotations from.

    Returns:
        a new quantum circuit that contains all the instructions from the provided
        circuit except annotations that are not TICK instructions.`
    """
    new_circuit = stim.Circuit()
    for inst in circuit:
        if isinstance(inst, stim.CircuitRepeatBlock):
            new_circuit.append(
                stim.CircuitRepeatBlock(
                    repeat_count=inst.repeat_count,
                    body=remove_annotations(inst.body_copy(), annotations_to_remove),
                )
            )
        elif not is_annotation(inst) or inst.name not in annotations_to_remove:
            new_circuit.append(inst)
    return new_circuit


def _offset_detectors(
    detectors: list[stim.CircuitInstruction], offset: int
) -> list[stim.CircuitInstruction]:
    offset_detectors: list[stim.CircuitInstruction] = []
    for detector in detectors:
        targets = [stim.target_rec(t.value - offset) for t in detector.targets_copy()]
        offset_detectors.append(
            stim.CircuitInstruction("DETECTOR", targets, detector.gate_args_copy())
        )
    return offset_detectors


def detector_to_targets_tuple(instruction: stim.CircuitInstruction) -> tuple[int, ...]:
    return tuple(t.value for t in instruction.targets_copy())


def push_all_detectors_to_the_end(circuit: stim.Circuit) -> stim.Circuit:
    new_circuit = stim.Circuit()
    detectors: list[stim.CircuitInstruction] = []
    for instruction in circuit:
        if isinstance(instruction, stim.CircuitRepeatBlock):
            new_circuit.append(
                stim.CircuitRepeatBlock(
                    instruction.repeat_count,
                    push_all_detectors_to_the_end(instruction.body_copy()),
                )
            )
        elif is_measurement(instruction):
            num_targets = len(instruction.targets_copy())
            detectors = _offset_detectors(detectors, num_targets)
            new_circuit.append(instruction)
        elif instruction.name == "DETECTOR":
            detectors.append(instruction)
        else:
            new_circuit.append(instruction)

    for detector in sorted(detectors, key=detector_to_targets_tuple, reverse=True):
        new_circuit.append(detector)
    return new_circuit
