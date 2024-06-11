from __future__ import annotations

from dataclasses import dataclass

import stim
from tqec.circuit.detectors.pauli import PauliString
from tqec.circuit.detectors.utils import (
    collapse_pauli_strings_at_moment,
    has_circuit_repeat_block,
    has_measurement,
    has_only_measurement,
    has_only_reset,
    has_reset,
    is_virtual_moment,
    iter_stim_circuit_by_moments,
    split_combined_measurement_reset_in_moment,
)
from tqec.exceptions import TQECException


class Fragment:
    def __init__(self, circuit: stim.Circuit):
        """A sub-circuit guaranteed to start with a moment filled by reset instructions
        and to end with a moment filled by measurement instructions.

        A Fragment instance is guaranteed to start with resets and to end with
        measurements.
        Moreover, if there is a collapsing operation (reset or measurement) between two
        `TICK` annotation then all the operations between these two `TICK` are of the
        same type.

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
            if not has_only_reset(moment):
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
            if not has_only_measurement(moment):
                raise TQECException(
                    "Breaking invariant: found a moment with at least one measurement "
                    f"instruction and a non-measurement instruction:\n{moment}"
                )
            # Insert new measurement at the front to keep them correctly ordered.
            self._measurements = (
                collapse_pauli_strings_at_moment(moment) + self._measurements
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
        """Get the measurement instructions at the front on the Fragment.

        Returns:
            all the measirement instructions that appear at the end of the represented
            circuit, in the order of appearance, and in increasing qubit order for
            measurements that are performed in parallel.
        """
        return self._measurements

    @property
    def measurements_qubits(self) -> list[int]:
        qubits = []
        for measurement in self.measurements:
            (qubit,) = measurement.qubits
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


@dataclass(frozen=True)
class FragmentLoop:
    fragments: list[Fragment | FragmentLoop]
    repetitions: int

    def __post_init__(self):
        if self.repetitions < 1:
            raise TQECException(
                "Cannot have a FragmentLoop with 0 or less repetitions."
            )

    def with_repetitions(self, repetitions: int) -> FragmentLoop:
        return FragmentLoop(fragments=self.fragments, repetitions=repetitions)

    def __repr__(self) -> str:
        return f"FragmentLoop(repetitions={self.repetitions}, fragments={self.fragments!r})"


def split_stim_circuit_into_fragments(
    circuit: stim.Circuit,
) -> list[Fragment | FragmentLoop]:
    """Split the circuit into fragments.

    The provided circuit should check a few pre-conditions:

    - If there is one measurement (resp. reset) instruction between two TICK
      annotation, then only measurement (resp. reset) instructions, annotations
      and noisy gates can appear between these two TICK. Any other instruction
      will result in an exception being raised.

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
    for moment in iter_stim_circuit_by_moments(circuit):
        # If we have a REPEAT block
        if isinstance(moment, stim.CircuitRepeatBlock):
            # Purge the current fragment
            if current_fragment:
                fragments.append(Fragment(current_fragment.copy()))
                current_fragment.clear()
            # Recurse to produce the Fragment instances for the loop body.
            try:
                body_fragments = split_stim_circuit_into_fragments(moment.body_copy())
            except TQECException as e:
                raise TQECException(
                    f"Error when splitting the following REPEAT block:\n{moment.body_copy()}"
                ) from e
            fragments.append(
                FragmentLoop(fragments=body_fragments, repetitions=moment.repeat_count)
            )
        # If this is a combined measurement/reset moment
        elif has_only_measurement(moment) and has_reset(moment):
            measurements, resets = split_combined_measurement_reset_in_moment(moment)
            current_fragment += measurements
            fragments.append(Fragment(current_fragment.copy()))
            current_fragment.clear()
            current_fragment += resets
        # If this is a measurement moment
        elif has_only_measurement(moment):
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
        if has_only_reset(current_fragment):
            raise TQECException(
                "Found left-over reset gates when splitting a circuit. Make "
                "sure that each reset (even resets from measurement/reset "
                "combined instruction) is eventually followed by a measurement. "
                f"Unprocessed fragment:\n{current_fragment}"
            )
        raise TQECException(
            "Circuit splitting did not finish on a measurement. "
            f"Unprocessed fragment: \n{current_fragment}"
        )
    return fragments
