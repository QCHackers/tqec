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
        - TICK instructions can only appear at the end of a `stim.Circuit`
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


def _is_measurement(instruction: stim.CircuitInstruction) -> bool:
    return instruction.name in ["M", "MR", "MRX", "MRY", "MRZ", "MX", "MY", "MZ"]


def _is_reset(instruction: stim.CircuitInstruction) -> bool:
    return stim.gate_data(instruction.name).is_reset  # type: ignore


def _is_noisy_gate(instruction: stim.CircuitInstruction) -> bool:
    return (
        not _is_measurement(instruction)
        and stim.gate_data(instruction.name).is_noisy_gate
    )


def _is_annotation(instruction: stim.CircuitInstruction) -> bool:
    return instruction.name in ANNOTATIONS


def _is_virtual_instruction(inst: stim.CircuitInstruction) -> bool:
    return _is_annotation(inst) or _is_noisy_gate(inst)  # type: ignore


def _is_combined_measurement_reset(instruction: stim.CircuitInstruction) -> bool:
    return _is_measurement(instruction) and _is_reset(instruction)


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
        if _is_virtual_instruction(inst):  # type: ignore
            continue
        if _is_combined_measurement_reset(inst):  # type: ignore
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
    return any(_is_measurement(inst) for inst in moment)  # type:ignore


def has_only_measurement(moment: stim.Circuit) -> bool:
    """Check if a `stim.Circuit` moment contains only measurement instructions.

    Note:
        Annotations are ignored by this function.

    Args:
        moment: The moment to check.

    Returns:
        `True` if the provided moment has a measurement, else `False`.
    """
    for inst in moment:
        if _is_virtual_instruction(inst):  # type: ignore
            continue
        if not _is_measurement(inst):  # type: ignore
            return False
    return True


def has_reset(moment: stim.Circuit) -> bool:
    """Check if a `stim.Circuit` moment contains reset instructions.

    Args:
        moment: The moment to check.

    Returns:
        `True` if the provided moment has a reset, else `False`.
    """
    return any(_is_reset(inst) for inst in moment)  # type:ignore


def has_only_reset(moment: stim.Circuit) -> bool:
    """Check if a `stim.Circuit` moment contains only reset instructions.

    Note:
        Annotations are ignored by this function.

    Args:
        moment: The moment to check.

    Returns:
        `True` if the provided moment has a reset, else `False`.
    """
    for inst in moment:
        if _is_virtual_instruction(inst):  # type: ignore
            continue
        if not _is_reset(inst):  # type: ignore
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
    return all(_is_virtual_instruction(inst) for inst in moment)  # type:ignore


def split_combined_measurement_reset_in_moment(
    moment: stim.Circuit,
) -> tuple[stim.Circuit, stim.Circuit]:
    """Split a moment that contains combined operations into two moments.

    The moment should only contain annotations, noisy operations, or combined
    measurement/reset operations.

    Warning:
        This function assumes that any annotation encountered in the provided
        moment should appear just after all the measurements:
        ```
        measurements - TICK - resets
                     ^
            All annotations are inserted here.
        ```
        This assumption seems reasonable for `DETECTOR` and `OBSERVABLE_INCLUDE`
        annotations, which are expected to be the most commonly found in a
        combined measurement/reset moment.
        Nevertheless, be aware of that limitation when using that function.

    Args:
        moment: a valid moment (i.e., sub-circuit contained between two TICK
            instructions) containing only measurement or combined instructions.

    Raises:
        TQECException: if the provided moment contains a stim.CircuitRepeatBlock
            instruction.

    Returns:
        two `stim.Circuit` instances `(measurements, resets)` that repectively
        contain all measurements and all resets found in the provided `moment`.
        The returned `measurements` circuit is guaranteed to finish by a TICK
        instruction.
        The returned `resets` circuit is guaranteed to not finish by a TICK
        instruction.
        `measurements` is guaranteed to contain all the instructions that appeared
        before the combined operation.
        `resets` is guaranteed to contain all the instructions that appeared
        after the combined operation.

    """
    measurements = stim.Circuit()
    resets = stim.Circuit()

    measured_qubits: set[int] = set()
    tick_instruction_encountered: bool = False
    for inst in moment:
        if isinstance(inst, stim.CircuitRepeatBlock):
            raise TQECException(
                "Breaking invariant: stim.CircuitRepeatBlock instances are not "
                "allowed in split_combined_measurement_reset_in_moment. Did you "
                "provide a moment obtained from calling iter_stim_circuit_by_moments?"
            )
        if inst.name == "TICK":
            # In theory, we are in a moment here, so we should only find TICK instructions
            # at the end of the circuit. To avoid adding too much TICK instructions, and
            # because TICK instructions are appropriately added at the end of that function,
            # we filter out any TICK instruction here.
            tick_instruction_encountered = True
            continue
        if _is_annotation(inst):
            # We expect annotations (DETECTOR, OBSERVABLE_INCLUDE, ...) to make sense
            # after measurements rather than after resets. This might be a wrong
            # assumption, so this might change in the future.
            measurements.append(inst)
            continue
        if not all(t.is_qubit_target for t in inst.targets_copy()):
            # The only instructions that might not have qubit targets are DETECTOR or
            # OBSERVABLE_INCLUDE annotations, that have already been handled before and
            # so should never reach this point.
            raise TQECException(
                f"Could not split with gate that have non-qubit targets. Found {inst}."
            )
        # Have to be of that type as checked above.
        targets: list[object] = list(inst.targets_copy())
        qubit_targets: set[int] = {t.qubit_value for t in inst.targets_copy()}  # type:ignore
        if _is_combined_measurement_reset(inst):
            if qubit_targets & measured_qubits:
                raise TQECException(
                    "Found an instruction on an already measured qubit, did you really "
                    "provide a *moment* or rather a full circuit? Consider calling "
                    "split_combined_measurement_reset for a full circuit."
                )
            if inst.name in ["MR", "MRZ"]:
                measurements.append(stim.CircuitInstruction("M", targets))
                resets.append(stim.CircuitInstruction("R", targets))
            elif inst.name in ["MRX", "MRY"]:
                meas_name = f"M{inst.name[2]}"
                measurements.append(stim.CircuitInstruction(meas_name, targets))
                resets.append(stim.CircuitInstruction(inst.name[1:], targets))
            measured_qubits |= qubit_targets
        elif _is_measurement(inst):
            measurements.append(inst)
            measured_qubits |= qubit_targets
        elif _is_reset(inst):
            resets.append(inst)
            if not qubit_targets.issubset(measured_qubits):
                raise TQECException(
                    "Found a reset on a non-measured qubit. Should that be allowed?\n"
                    f"Moment:\n{moment}"
                )
        else:
            # An annotation or a noisy instruction.
            # If none of the qubits the instruction is applied on has already been
            # measured, this means that we can insert the instruction in measurements.
            if not qubit_targets & measured_qubits:
                measurements.append(inst)
            # Else, if all the qubits the instruction is applied on has already been
            # measured, this means that we can insert the instruction in resets.
            elif qubit_targets.issubset(measured_qubits):
                resets.append(inst)
            # Else, some of the qubits have been measured and others have not, this is
            # not supposed to happen.
            else:
                raise TQECException(
                    "Found an instruction applied on partially measured qubits.\n"
                    f"The instruction: {inst}\n"
                    f"Measured qubits: {measured_qubits}"
                )

    # Ensure that measurements ends with a TICK operation and that resets does
    # only if a TICK instruction has been encountered when iterating on instructions.
    # As TICK instructions are filtered out early when interating on instructions,
    # neither measurements nor resets should have a TICK instruction, so we can add
    # the instruction without checking for 
    measurements.append(stim.CircuitInstruction("TICK", []))
    if tick_instruction_encountered:
        resets.append(stim.CircuitInstruction("TICK", []))
    return measurements, resets


def split_combined_measurement_reset(circuit: stim.Circuit) -> stim.Circuit:
    """Replace all the combined measurement/reset instructions with 1 measurement
    and 1 reset.

    Args:
        circuit: original circuit that may contain combined instruction.

    Returns:
        a copy of the provided `circuit`, but with combined operations replaced by
        2 instructions.
    """
    new_circuit = stim.Circuit()
    for moment in iter_stim_circuit_by_moments(circuit):
        if isinstance(moment, stim.CircuitRepeatBlock):
            new_circuit.append(
                stim.CircuitRepeatBlock(
                    body=split_combined_measurement_reset(moment.body_copy()),
                    repeat_count=moment.repeat_count,
                )
            )
        elif has_combined_measurement_reset(moment):
            measurements, resets = split_combined_measurement_reset_in_moment(moment)
            new_circuit += measurements
            new_circuit += resets
        else:
            new_circuit += moment
    return new_circuit


def pauli_string_mean_coords(
    pauli_string: PauliString, qubit_coords_map: dict[int, list[float]]
) -> tuple[float, ...]:
    all_coords_items = [qubit_coords_map[i] for i in pauli_string.qubits]
    return tuple(numpy.mean(numpy.asarray(all_coords_items), axis=0)) + (0.0,)


def _collapsing_inst_to_pauli_strings(
    inst: stim.CircuitInstruction,
) -> list[PauliString]:
    """Create the `PauliString` instances representing the provided collapsing instruction.

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
    """Compute and return the list of PauliString instances representing all the
    collapsing operations found in the provided moment.

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
        if _is_virtual_instruction(inst):  # type: ignore
            continue
        collapsing_operations = _collapsing_inst_to_pauli_strings(inst)  # type: ignore
        collapsing_operations_sorted_by_qubit = sorted(
            collapsing_operations, key=lambda ps: ps.qubit
        )
        pauli_strings.extend(collapsing_operations_sorted_by_qubit)
    return pauli_strings
