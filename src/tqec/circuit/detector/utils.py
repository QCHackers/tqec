import typing as ty

import numpy
import stim
from tqec.circuit.detector.pauli import PauliString
from tqec.exceptions import TQECException

ANNOTATIONS = {
    "QUBIT_COORDS",
    "DETECTOR",
    "OBSERVABLE_INCLUDE",
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


def has_measurement(
    moment: stim.Circuit, check_are_all_measurements: bool = False
) -> bool:
    """Check if a `stim.Circuit` moment contains measurement instructions.

    Args:
        moment (stim.Circuit): The moment to check.
        check_are_all_measurements (bool, optional): If `True`, when the moment contains a
            measurement, then all instructions except for annotations and noise instructions
            must be measurement instructions, otherwise an exception is raised.
            Defaults to `False`.

    Raises:
        TQECException: If `check_are_all_measurement == True`, at least one instruction
        in the provided moment is a measurement, and at least one instruction is
        not a measurement.

    Returns:
        bool: `True` if the provided moment has a measurement, else `False`.
    """
    if not any(stim.gate_data(inst.name).produces_measurements for inst in moment):
        return False
    if not check_are_all_measurements:
        return True
    for inst in moment:
        if stim.gate_data(inst.name).is_noisy_gate or inst.name in ANNOTATIONS:
            continue
        if not stim.gate_data(inst.name).produces_measurements:
            raise TQECException(
                f"The measurement moment contains non-measurement instruction: {inst}."
            )
    return True


def has_reset(moment: stim.Circuit, check_are_all_resets: bool = False) -> bool:
    """Check if a `stim.Circuit` moment contains reset instructions.

    Args:
        moment (stim.Circuit): The moment to check.
        check_are_all_resets (bool, optional): If `True`, when the moment contains a
            reset, then all instructions except for annotations and noise instructions
            must be reset instructions, otherwise an exception is raised.
            Defaults to `False`.

    Raises:
        TQECException: If `check_are_all_resets == True`, at least one instruction
            in the provided moment is a reset, and at least one instruction is
            not a reset.

    Returns:
        bool: `True` if the provided moment has a reset, else `False`.
    """
    if not any(stim.gate_data(inst.name).is_reset for inst in moment):
        return False
    if not check_are_all_resets:
        return True
    for inst in moment:
        # note that measurements are noisy gates by define in stim
        if (
            stim.gate_data(inst.name).is_noisy_gate
            and not stim.gate_data(inst.name).produces_measurements
            or inst.name in ANNOTATIONS
        ):
            continue
        if not stim.gate_data(inst.name).is_reset:
            raise TQECException(
                f"The reset moment contains non-reset instruction: {inst}."
            )
    return True


def pauli_string_mean_coords(
    pauli_string: PauliString, qubit_coords_map: dict[int, list[float]]
) -> tuple[float, ...]:
    all_coords_items = [qubit_coords_map[i] for i in pauli_string.qubit2pauli.keys()]
    return tuple(numpy.mean(numpy.asarray(all_coords_items), axis=0)) + (0.0,)
