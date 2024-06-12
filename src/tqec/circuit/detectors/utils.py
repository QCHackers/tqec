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
    measurement/reset operations. Combined operations should appear in one block.

    Args:
        moment: a valid moment (i.e., sub-circuit contained between two TICK
            instructions) containing only measurement or combined instructions.

    Raises:
        TQECException: if the provided moment contains a stim.CircuitRepeatBlock
            instruction.

    Returns:
        two `stim.Circuit` instances `(measurements, resets)` that repectively
        contain all measurements and all resets found in the provided `moment`.
        The two returned circuits are guaranteed to finish by a TICK instruction.
        `measurements` is guaranteed to contain all the instructions that appeared
        before the combined operation.
        `resets` is guaranteed to contain all the instructions that appeared
        after the combined operation.

    """
    measurements = stim.Circuit()
    resets = stim.Circuit()

    # Checking pre-condition:
    for inst in moment:
        if isinstance(inst, stim.CircuitRepeatBlock):
            raise TQECException(
                "Breaking invariant: stim.CircuitRepeatBlock instances are not "
                "allowed in split_combined_measurement_reset_in_moment. Did you "
                "provide a moment obtained from calling iter_stim_circuit_by_moments?"
            )

    i: int = 0
    # First, non-measurements that might be noisy gates such as X_ERROR.
    while i < len(moment) and not _is_measurement(moment[i]):  # type:ignore
        measurements.append(moment[i])
        i += 1
    # Then, combined reset/measurement instructions
    while i < len(moment) and _is_measurement(moment[i]) and _is_reset(moment[i]):  # type:ignore
        inst = moment[i]
        targets: list[object] = list(inst.targets_copy())  # type:ignore
        if inst.name in ["MR", "MRZ"]:
            measurements.append(stim.CircuitInstruction("M", targets))
            resets.append(stim.CircuitInstruction("R", targets))
        elif inst.name in ["MRX", "MRY"]:
            meas_name = f"M{inst.name[2]}"
            measurements.append(stim.CircuitInstruction(meas_name, targets))
            resets.append(stim.CircuitInstruction(inst.name[1:], targets))
        i += 1
    # Finally again, non-measurements that might be noisy gates such as X_ERROR.
    while i < len(moment) and not (_is_measurement(moment[i]) or _is_reset(moment[i])):  # type:ignore
        resets.append(moment[i])
        i += 1
    # If the previous loop did not exhaust the circuit gates, this is an error.
    if i < len(moment):
        raise TQECException(
            "Could not correctly split combined instruction. "
            "Did you ensure that the pre-conditions were checked?"
        )
    # Ensure that both measurements and resets end with a TICK operation
    for m in (measurements, resets):
        if m[-1].name != "TICK":
            m.append(stim.CircuitInstruction("TICK", []))
    return measurements, resets


def split_combined_measurement_reset(circuit: stim.Circuit) -> stim.Circuit:
    """Replace all the combined measurement/reset instructions with 1 measurement and 1 reset.

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

    return sorted(
        (
            pauli_string
            for inst in moment
            if not _is_virtual_instruction(inst)  # type: ignore
            for pauli_string in _collapsing_inst_to_pauli_strings(inst)  # type: ignore
        ),
        key=lambda ps: next(iter(ps.qubits)),
    )
