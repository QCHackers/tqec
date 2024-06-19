from __future__ import annotations

import typing as ty
import warnings
from dataclasses import dataclass

import stim
from tqec.circuit.detectors.pauli import PauliString
from tqec.circuit.detectors.utils import (
    collapse_pauli_strings_at_moment,
    has_circuit_repeat_block,
    has_measurement,
    has_only_measurement_or_is_virtual,
    has_only_reset_or_is_virtual,
    has_reset,
    is_virtual_moment,
    iter_stim_circuit_by_moments,
    split_combined_measurement_reset_in_moment,
    split_moment_containing_measurements,
)
from tqec.exceptions import TQECException


class Fragment:
    def __init__(self, circuit: stim.Circuit):
        """A sub-circuit guaranteed to end with a moment filled by measurement instructions.

        Fragment instances represent sub-circuits that contain:

        1. zero or more moments exclusively composed of `reset`, annotation or
            noisy-gate instructions,
        2. zero or more moments composed of "computation" instructions (anything
            that is not a measurement or a reset),
        3. one or more moments exclusively composed of `measurement`, annotation
            or noisy-gate instructions.

        Raises:
            TQECException: if the provided `stim.Circuit` instance contains a
                stim.CircuitRepeatBlock instance.
            TQECException: if any moment from the provided circuit contains
                both a measurement (resp. reset) and a non-measurement (resp.
                non-reset) operation. Note that annotations and noisy-gates
                instructions (measurements excluded) are ignored, and so are
                excluded from this condition.
            TQECException: if the provided circuit does not end with at least
                one measurement.

        Args:
            circuit: the circuit represented by the instance.
        """
        if has_circuit_repeat_block(circuit):
            raise TQECException(
                "Breaking invariant: Cannot initialise a Fragment with a "
                "stim.CircuitRepeatBlock instance but found one. Did you "
                "meant to use FragmentLoop?"
            )
        # The line below has no type issue as the circuit does not contain
        # any stim.CircuitRepeatBlock instance, and so iter_stim_circuit_by_moments
        # can only return stim.Circuit instances.
        moments = [moment.copy() for moment in iter_stim_circuit_by_moments(circuit)]  # type: ignore

        self._circuit = circuit
        self._resets: list[PauliString] = []
        self._measurements: list[PauliString] = []

        for moment in moments:
            if is_virtual_moment(moment):
                continue
            if not has_reset(moment):
                break
            if not has_only_reset_or_is_virtual(moment):
                raise TQECException(
                    "Breaking invariant: found a moment with at least one reset "
                    f"instruction and a non-reset instruction:\n{moment}"
                )
            self._resets.extend(collapse_pauli_strings_at_moment(moment))

        for moment in reversed(moments):
            if is_virtual_moment(moment):
                continue
            if not has_measurement(moment):
                break
            if not has_only_measurement_or_is_virtual(moment):
                raise TQECException(
                    "Breaking invariant: found a moment with at least one measurement "
                    f"instruction and a non-measurement instruction:\n{moment}"
                )
            # Insert new measurement at the front to keep them correctly ordered.
            self._measurements = (
                collapse_pauli_strings_at_moment(moment) + self._measurements
            )

        if not self._measurements:
            raise TQECException(
                "A Fragment should end with at least one measurement. "
                "The provided circuit does not seem to check that condition.\n"
                f"Provided circuit:\n{circuit}"
            )

    @property
    def resets(self) -> list[PauliString]:
        """Get the reset instructions at the front on the Fragment.

        Returns:
            all the reset instructions that appear at the beginning of the represented
            circuit, in the order of appearance, and in increasing qubit order for resets
            that are performed in parallel.
        """
        return self._resets

    @property
    def measurements(self) -> list[PauliString]:
        """Get the measurement instructions at the back on the Fragment.

        Returns:
            all the measurement instructions that appear at the end of the represented
            circuit, in the order of appearance, and in increasing qubit order for
            measurements that are performed in parallel.
        """
        return self._measurements

    @property
    def measurements_qubits(self) -> list[int]:
        qubits = []
        for measurement in self.measurements:
            qubit = measurement.qubit
            qubits.append(qubit)
        return qubits

    @property
    def num_measurements(self) -> int:
        return len(self._measurements)

    @property
    def circuit(self) -> stim.Circuit:
        return self._circuit

    def get_tableau(self) -> stim.Tableau:
        return self._circuit.to_tableau(
            ignore_measurement=True, ignore_noise=True, ignore_reset=True
        )

    def __repr__(self) -> str:
        return f"Fragment(circuit={self._circuit!r})"

    def __eq__(self, other: Fragment) -> bool:
        if not isinstance(other, Fragment):
            return False
        return self._circuit == other._circuit


@dataclass(frozen=True)
class FragmentLoop:
    fragments: list[Fragment | FragmentLoop]
    repetitions: int

    def __post_init__(self):
        if self.repetitions < 1:
            raise TQECException(
                "Cannot have a FragmentLoop with 0 or less repetitions."
            )
        if not self.fragments:
            raise TQECException(
                "Cannot initialise a FragmentLoop instance without any "
                "fragment for the loop body."
            )

    def with_repetitions(self, repetitions: int) -> FragmentLoop:
        return FragmentLoop(fragments=self.fragments, repetitions=repetitions)

    def __repr__(self) -> str:
        return f"FragmentLoop(repetitions={self.repetitions}, fragments={self.fragments!r})"


def _get_fragment_loop(repeat_block: stim.CircuitRepeatBlock) -> FragmentLoop:
    try:
        body_fragments = split_stim_circuit_into_fragments(repeat_block.body_copy())
    except TQECException as e:
        raise TQECException(
            f"Error when splitting the following REPEAT block:\n{repeat_block.body_copy()}"
        ) from e
    return FragmentLoop(fragments=body_fragments, repetitions=repeat_block.repeat_count)


def _consume_measurements(
    moments_iterator: ty.Iterator[stim.Circuit | stim.CircuitRepeatBlock],
) -> tuple[stim.Circuit, stim.Circuit | stim.CircuitRepeatBlock]:
    measurements = stim.Circuit()

    for moment in moments_iterator:
        # If we find an instance of stim.CircuitRepeatBlock, the sequence
        # of measurements is over, so simply return.
        if isinstance(moment, stim.CircuitRepeatBlock):
            return measurements, moment
        # Else, if the moment only contains annotations and noisy-gates
        # (measurements excluded), add it to the measurements.
        elif is_virtual_moment(moment):
            measurements += moment
        # Else, if there is at least one measurement in the moment:
        elif has_measurement(moment):
            if not has_only_measurement_or_is_virtual(moment):
                # if the moment contains at least one measurement and one
                # non-measurement, split measurements from non-measurements
                # and return.
                final_measurements, left_over = split_moment_containing_measurements(
                    moment
                )
                return measurements + final_measurements, left_over
            # Else, if any reset is found, the moment contains at least one combined
            # measurement/reset operation so split all combined operations, and
            # directly return because the reset found ends the measurement
            # sequence.
            if has_reset(moment):
                final_measurements, left_over = (
                    split_combined_measurement_reset_in_moment(moment)
                )
                return measurements + final_measurements, left_over
            # Else, there is no reset, so we have a moment filled with normal
            # measurements. Just add them to the list of measurements, and
            # continue.
            measurements += moment
        # The moment is not virtual (i.e., not filled with only annotations and
        # noisy gates, so it contains a non-virtual gate) and does not have any
        # measurement (so the non-virtual gate is not a measurement). This ends the
        # measurement sequence, so return.
        else:
            return measurements, moment

    # We exhausted the provided iterator, this is the circuit end,
    # so return the measurements that have been seen.
    return measurements, stim.Circuit()


def split_stim_circuit_into_fragments(
    circuit: stim.Circuit,
) -> list[Fragment | FragmentLoop]:
    """Split the circuit into fragments.

    The provided circuit should check a few pre-conditions:

    - If there is one measurement (resp. reset) instruction between two TICK
      annotation, then only measurement (resp. reset) instructions, annotations
      and noisy gates can appear between these two TICK. Any other instruction
      will result in an exception being raised.
    - The circuit should be (recursively if it contains one or more instance of
      `stim.CircuitRepeatBlock`) composed of a succession of layers that should
      have the same shape:

      - starts with zero or more moments containing exclusively reset operations,
      - continuing with zero or more moments containing any non-collapsing operation
        (i.e., anything except reset and measurement operations).
      - ends with one or more moments containing exclusively measurement operations.

      For this reason, be careful with reset/measurement combined operations (e.g.,
      the `stim` instruction `MR` that performs in one instruction a measurement and
      a reset in the Z basis). These instructions are replaced by their non-combined
      equivalent (e.g., the `MR` operation is replaced by a `M` operation, followed
      by a `R` operation), and the resulting circuit should check the above
      pre-condition.

    Args:
        circuit (stim.Circuit): the circuit to split into Fragment instances.

    Raises:
        TQECException: If the circuit contains at least one moment (i.e., group of
            instructions between two TICK annotations) that are composed of at least
            one measurement (resp. one reset) and at least one non-annotation,
            non-measurement (resp. non-reset) instruction.

    Returns:
        the resulting fragments.
    """
    fragments: list[Fragment | FragmentLoop] = []

    current_fragment = stim.Circuit()

    moments_iterator = iter_stim_circuit_by_moments(circuit)
    for moment in moments_iterator:
        # If we have a REPEAT block
        if isinstance(moment, stim.CircuitRepeatBlock):
            # Purge the current fragment.
            # Note that the following lines should only be triggered on invalid
            # inputs as once one measurement is found, all the following measurements
            # are collected and a Fragment instance is created (see content of next
            # elif branch). So if we are here and there is some partially collected
            # fragment (i.e., current_fragment is not empty), it means that it is
            # not terminated by measurements, which will raise an error when Fragment
            # is constructed.
            if current_fragment:
                raise TQECException(
                    "Trying to start a REPEAT block without a cleanly finished Fragment. "
                    "The following instructions were found preceding the REPEAT block:\n"
                    + "\n\t".join(f"{m}" for m in current_fragment)
                    + "\nbut these instructions do not form a valid Fragment."
                )
            # Recurse to produce the Fragment instances for the loop body.
            fragments.append(_get_fragment_loop(moment))

        # If this is a measurement moment
        elif has_measurement(moment):
            # If there is something else than measurements, just split the something else
            # out, add the measurements to the current Fragment, build it, and start a
            # new one with the something else.
            if not has_only_measurement_or_is_virtual(moment):
                measurements, left_over = split_moment_containing_measurements(moment)
                current_fragment += measurements
                fragments.append(Fragment(current_fragment.copy()))
                current_fragment.clear()
                current_fragment += left_over
                continue
            # Else, we only have measurements in this moment, so we can:
            # 1. add the full moment to the current fragment,
            current_fragment += moment
            # 2. try to find more subsequent measurements in the following moments,
            more_measurements, left_over = _consume_measurements(moments_iterator)
            # 3. finish the current fragment with the found measurements
            current_fragment += more_measurements
            fragments.append(Fragment(current_fragment.copy()))
            current_fragment.clear()
            # 4. handle the left over instructions.
            if isinstance(left_over, stim.CircuitRepeatBlock):
                fragments.append(_get_fragment_loop(left_over))
            else:
                current_fragment += left_over

        # This is either a regular instruction or a reset moment. In any case,
        # just add it to the current fragment.
        else:
            current_fragment += moment

    # If current_fragment is not empty here, this means that the circuit did not finish
    # with a measurement. This is strange, so for the moment raise an exception.
    if current_fragment:
        if has_only_reset_or_is_virtual(current_fragment):
            warnings.warn(
                "Found left-over reset gates when splitting a circuit. Make "
                "sure that each reset (even resets from measurement/reset "
                "combined instruction) is eventually followed by a measurement. "
                f"Unprocessed fragment:\n{current_fragment}",
                RuntimeWarning,
            )
        else:
            raise TQECException(
                "Circuit splitting did not finish on a measurement. "
                f"Unprocessed fragment: \n{current_fragment}"
            )
    return fragments
