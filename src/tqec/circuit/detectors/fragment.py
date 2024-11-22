from __future__ import annotations

import typing
import warnings
from dataclasses import dataclass

import stim

from tqec.circuit.detectors.pauli import PauliString
from tqec.circuit.detectors.predicates import is_valid_input_circuit
from tqec.circuit.detectors.utils import (
    collapse_pauli_strings_at_moment,
    has_circuit_repeat_block,
    has_measurement,
    has_only_measurement_or_is_virtual,
    has_only_reset_or_is_virtual,
    has_reset,
    is_virtual_moment,
    iter_stim_circuit_by_moments,
)
from tqec.exceptions import TQECException, TQECWarning


class Fragment:
    def __init__(self, circuit: stim.Circuit):
        """A sub-circuit guaranteed to end with a moment filled by measurement
        instructions.

        Fragment instances represent sub-circuits that contain:

        1. zero or more moments exclusively composed of `reset`, annotation or
            noisy-gate instructions,
        2. zero or more moments composed of "computation" instructions (anything
            that is not a measurement or a reset),
        3. one moment exclusively composed of `measurement`, annotation
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
        moments = [
            typing.cast(stim.Circuit, moment).copy()
            for moment in iter_stim_circuit_by_moments(circuit)
        ]

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
        qubits: list[int] = []
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

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Fragment) and self._circuit == other._circuit


@dataclass(frozen=True)
class FragmentLoop:
    fragments: list[Fragment | FragmentLoop]
    repetitions: int

    def __post_init__(self) -> None:
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
      - ends with one moment containing exclusively measurement operations.

      For the above reasons, be careful with reset/measurement combined operations
      (e.g., the `stim` instruction `MR` that performs in one instruction a
      measurement and a reset in the Z basis). These instructions are not supported
      by the `tqec` library and it is up to the user to check that the input circuit
      does not contain combined measurements/resets instructions.

    Args:
        circuit (stim.Circuit): the circuit to split into Fragment instances.

    Raises:
        TQECException: If the circuit contains at least one moment (i.e., group of
            instructions between two TICK annotations) that are composed of at least
            one measurement (resp. one reset) and at least one non-annotation,
            non-measurement (resp. non-reset) instruction.
        TQECException: If the circuit contains combined measurement/reset instructions.
        TQECException: If the provided circuit could not be split into fragments due
            to an invalid structure.

    Returns:
        the resulting fragments.
    """
    potential_error_reason = is_valid_input_circuit(circuit)
    if potential_error_reason is not None:
        raise TQECException(potential_error_reason)

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
            # If there is something else than measurements, raise because this is
            # not a valid input.
            if not has_only_measurement_or_is_virtual(moment):
                raise TQECException(
                    "A moment with at least one measurement instruction can "
                    "only contain measurements."
                )
            # Else, we only have measurements in this moment, so we can
            # add the full moment to the current fragment and start a new one.
            current_fragment += moment
            fragments.append(Fragment(current_fragment.copy()))
            current_fragment.clear()

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
                TQECWarning,
            )
        else:
            raise TQECException(
                "Circuit splitting did not finish on a measurement. "
                f"Unprocessed fragment: \n{current_fragment}"
            )
    return fragments
