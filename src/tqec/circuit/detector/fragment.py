"""Introduces the necessary classes to split a `stim.Circuit` into fragments.

This module introduce the code notion of a fragment. A fragment is a contiguous
subset of a `stim.Circuit` instance that has collapsing operations (i.e.,
measurements or resets) on both sides (start and end). Reset operations might be
found in the `Fragment` instance before (see `sources_for_next_fragment`), and
so the `stim.Circuit` instance stored does not have to start by reset instructions
(as they can be in the previous `Fragment`) and might finish with reset instructions
instead of measurement ones.
Following that definition, a `Fragment` is defined as a subset of a `stim.Circuit`
(encoded as a `stim.Circuit` instance itself) and lists of stabilizers:

- `end_stabilizer_sources` that list the possible sources for stabilizers that
  might propagate forward to the end of the `Fragment`. These sources are
  necessarily reset operations.
- `begin_stabilizer_sources` that list the possible sources for stabilizers that
  might propagate backwards to the beginning of the `Fragment`. These sources are
  necessarily measurement operations.
- `sources_for_next_fragment` that list the possible sources for stabilizers that
  might propagate forward to the beginning of the next `Fragment`. These sources
  are necessarily reset operations, and are often due to the usage of instructions
  that combine measurements and resets (e.g., "MR" in `stim`).

Repeated blocks are handled by a specific `FragmentLoop` class that simply stores
the `Fragment` instances (or other `FragmentLoop` instances) representing the
inner body of the loop along with a number of repetitions.

The `split_stim_circuit_into_fragments` function perform the conversion from an
instance of `stim.Circuit` to a list of `Fragment`/`FragmentLoop` instances
splitting that `stim.Circuit` instance on collapsing operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import stim
from tqec.circuit.detector.pauli import PauliString, collapse_pauli_strings_at_moment
from tqec.circuit.detector.utils import (
    has_measurement,
    has_reset,
    iter_stim_circuit_by_moments,
)


@dataclass(frozen=True)
class Fragment:
    """A sub-circuit guaranteed to span the locations between two nearest collapsing
    moments or those outside the error detection regions.

    Attributes:
        circuit: the circuit represented by the instance.
        end_stabilizer_sources: sources (reset instructions) that generate the
            stabilizers that might be found at the end of the circuit.
        begin_stabilizer_sources: sources (measurement instructions) that generate
            the stabilizers that might be found at the beginning of the circuit.
        sources_for_next_fragment: sources (reset instructions) that generate
            stabilizers after the measurements of this Fragment instance and so
            should be accounted for in the next Fragment.
    """

    circuit: stim.Circuit
    end_stabilizer_sources: list[PauliString] = field(default_factory=list)
    begin_stabilizer_sources: list[PauliString] = field(default_factory=list)
    sources_for_next_fragment: list[PauliString] = field(default_factory=list)

    @property
    def have_detector_sources(self) -> bool:
        return bool(
            self.end_stabilizer_sources
            or self.begin_stabilizer_sources
            or self.sources_for_next_fragment
        )


@dataclass(frozen=True)
class FragmentLoop:
    fragments: list[Fragment | FragmentLoop]
    repetitions: int

    def with_repetitions(self, repetitions: int) -> FragmentLoop:
        return FragmentLoop(fragments=self.fragments, repetitions=repetitions)

    @property
    def have_detector_sources(self) -> bool:
        return any(fragment.have_detector_sources for fragment in self.fragments)


@dataclass
class SplitState:
    """Represents the current state of a circuit exploration.

    This dataclass is used to accumulate the information gained by exploring
    a circuit until a fragment can be produced with that information.

    Its goal is really to be a stupid accumulator, the logic being implemented
    by the user of that class.
    """

    cur_fragment: stim.Circuit = field(default_factory=stim.Circuit)
    end_stabilizer_sources: list[PauliString] = field(default_factory=list)
    sources_for_next_fragment: list[PauliString] = field(default_factory=list)
    begin_stabilizer_sources: list[PauliString] = field(default_factory=list)
    seen_reset_at_head: bool = False
    seen_measurement_at_tail: bool = False

    def clear(self) -> None:
        self.cur_fragment.clear()
        self.end_stabilizer_sources.clear()
        self.sources_for_next_fragment.clear()
        self.begin_stabilizer_sources.clear()
        self.seen_reset_at_head = False
        self.seen_measurement_at_tail = False

    def to_fragment(self) -> Fragment:
        return Fragment(
            circuit=self.cur_fragment.copy(),
            end_stabilizer_sources=list(self.end_stabilizer_sources),
            begin_stabilizer_sources=list(self.begin_stabilizer_sources),
            sources_for_next_fragment=list(self.sources_for_next_fragment),
        )


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
    fragments = []
    state = SplitState()
    # Iterate the whole circuit TICK by TICK
    for moment in iter_stim_circuit_by_moments(circuit):
        # If we have a REPEAT block
        if isinstance(moment, stim.CircuitRepeatBlock):
            # Purge the current split state by producing a Fragment before
            # producing the FragmentLoop for the current moment.
            if state.cur_fragment:
                fragments.append(state.to_fragment())
                state.clear()
            # Recurse to produce the Fragment instances for the loop body.
            body_fragments = split_stim_circuit_into_fragments(moment.body_copy())
            fragments.append(
                FragmentLoop(fragments=body_fragments, repetitions=moment.repeat_count)
            )
        # If this is a measurement moment
        elif has_measurement(moment, check_are_all_measurements=True):
            state.cur_fragment += moment
            state.begin_stabilizer_sources.extend(
                collapse_pauli_strings_at_moment(moment, is_reset=False)
            )
            state.seen_measurement_at_tail = True
            state.sources_for_next_fragment.extend(
                collapse_pauli_strings_at_moment(moment, is_reset=True)
                if has_reset(moment, check_are_all_resets=False)
                else []
            )
        # If this is a reset moment
        elif has_reset(moment, check_are_all_resets=True):
            pauli_strings = collapse_pauli_strings_at_moment(moment, is_reset=True)
            if state.seen_measurement_at_tail:
                state.cur_fragment += moment
                state.sources_for_next_fragment.extend(pauli_strings)
            elif state.seen_reset_at_head:
                state.cur_fragment += moment
                state.end_stabilizer_sources.extend(pauli_strings)
            else:
                if state.cur_fragment:
                    fragments.append(state.to_fragment())
                    state.clear()
                state.cur_fragment += moment
                state.end_stabilizer_sources.extend(pauli_strings)
                state.seen_reset_at_head = True
        # This is not a reset, not a measurement, and not a REPEAT block moment.
        # If we found measurements but did not generate the Fragment instance yet,
        # do it now and start a new Fragment with the current moment.
        elif state.seen_measurement_at_tail:
            fragments.append(state.to_fragment())
            state.clear()
            state.cur_fragment += moment
        # This is a regular instruction, just add it to the current Fragment.
        else:
            state.cur_fragment += moment
    # If there is any part of the circuit left, purge the split state by creating
    # one last Fragment with the left-over moments.
    if state.cur_fragment:
        fragments.append(state.to_fragment())
    return fragments
