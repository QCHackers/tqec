from __future__ import annotations

import dataclasses
import functools
import itertools
from typing import Iterable

import stim

from tqec.circuit.detector.detector_util import (
    Fragment,
    FragmentLoop,
    PauliString,
    pauli_string_mean_coords,
    split_stim_circuit_into_fragments,
)


def annotate_detectors_automatically(circuit: stim.Circuit) -> stim.Circuit:
    fragments = split_stim_circuit_into_fragments(circuit)
    return compile_fragments_to_circuit(
        fragments, qubit_coords_map=circuit.get_final_qubit_coordinates()
    )


@dataclasses.dataclass(frozen=True)
class BoundaryStabilizer:
    """Represents the state of a stabilizer on the boundary of a Fragment.

    Attributes:
        before_collapse: stabiliser before applying any collapsing operation.
        after_collapse: stabiliser after applying the collapsing operations in the
            moment.
        coords: TODO
        commute_collapse_indices: TODO
        anticommute_collapse_indices: TODO
        source_measurement_indices: TODO
    """

    before_collapse: PauliString
    after_collapse: PauliString
    coords: tuple[float, ...]
    commute_collapse_indices: frozenset[int] = frozenset()
    anticommute_collapse_indices: frozenset[int] = frozenset()
    source_measurement_indices: frozenset[int] | None = None

    @property
    def all_commute(self) -> bool:
        return not bool(self.anticommute_collapse_indices)

    @property
    def is_begin_stabilizer(self) -> bool:
        return self.source_measurement_indices is not None


@dataclasses.dataclass(frozen=True)
class MatchedDetector:
    """Represents an automatically computed detector."""

    coords: tuple[float, ...]
    measurement_indices: frozenset[int]


@dataclasses.dataclass
class State:
    """Singleton state to be used during detector construction.

    We always focus on the beginning of the current fragment, where the
    end stabilizers from the previous fragment and the beginning stabilizers
    of the current fragment intersect.

    Attributes:
        resets_passed_in: list of collapsing operations originating from reset
            instructions from the previous Fragment instance and performed after
            the instance measurements.
        previous_measurements: list of collapsing operations originating from
            the measurements found in the previous Fragment instance.
        end_stabilizers: list of stabilizers at the end of the previous Fragment
            instance.
    """

    resets_passed_in: list[PauliString]
    previous_measurements: list[PauliString]
    end_stabilizers: list[BoundaryStabilizer]

    def clear(self):
        self.resets_passed_in = list()
        self.previous_measurements = list()
        self.end_stabilizers = list()


def compile_fragments_to_circuit(
    fragments: Iterable[Fragment | FragmentLoop],
    qubit_coords_map: dict[int, list[float]],
) -> stim.Circuit:
    """Entry-point to generate a valid `stim.Circuit` from a list of Fragments.

    Args:
        fragments: the fragments that have been generated from the original circuit.
        qubit_coords_map: a mapping from qubit indices to their coordinates.

    Returns:
        a valid `stim.Circuit` instance with automatically computed detectors inserted.
    """
    all_qubits = sorted(qubit_coords_map.keys())
    state = State(
        resets_passed_in=list(),
        previous_measurements=list(),
        end_stabilizers=[
            BoundaryStabilizer(
                before_collapse=PauliString({q: "I"}),
                after_collapse=PauliString({q: "I"}),
                coords=tuple(qubit_coords_map[q]),
            )
            for q in all_qubits
        ],
    )
    out_circuit = stim.Circuit()
    _compile_fragments_into_circuit(
        fragments, state, out_circuit, qubit_coords_map, True
    )
    return out_circuit


def _compile_fragments_into_circuit(
    fragments: Iterable[Fragment | FragmentLoop],
    state: State,
    out_circuit: stim.Circuit,
    qubit_coords_map: dict[int, list[float]],
    compile_final_state_once_more: bool = False,
) -> None:
    """Compile the provided fragments into `out_circuit`, mutating the input parameters.

    Warning:
        This function **mutates** its parameters in-place.

    Args:
        fragments: the fragments composing the circuit to build.
        state: current state of the circuit building.
        out_circuit: circuit that will be built in-place.
        qubit_coords_map: a map associating qubit indices to their coordinates.
        compile_final_state_once_more: compile the final state at the end of the function,
            ensuring that no open end stabilizer is left at the end of the circuit.
            Defaults to False.
    """
    for fragment in fragments:
        _compile_fragment_into_circuit(fragment, state, out_circuit, qubit_coords_map)
    # clean up open end stabilizers at the end of circuit
    if compile_final_state_once_more:
        _compile_fragment_into_circuit(
            Fragment(
                circuit=stim.Circuit(),
                begin_stabilizer_sources=[
                    PauliString({q: "I"}) for q in sorted(qubit_coords_map.keys())
                ],
            ),
            state,
            out_circuit,
            qubit_coords_map,
        )


def _compile_fragment_into_circuit(
    fragment: Fragment | FragmentLoop,
    state: State,
    out_circuit: stim.Circuit,
    qubit_coords_map: dict[int, list[float]],
) -> None:
    if isinstance(fragment, FragmentLoop):
        _compile_fragment_loop_into_circuit(
            fragment, state, out_circuit, qubit_coords_map
        )
    else:
        _compile_atomic_fragment_into_circuit(
            fragment, state, out_circuit, qubit_coords_map
        )


def _compile_atomic_fragment_into_circuit(
    fragment: Fragment,
    state: State,
    out_circuit: stim.Circuit,
    qubit_coords_map: dict[int, list[float]],
) -> None:
    """Compile the provided fragment into the provided circuit.

    Warning:
        This function **mutates** its parameters in-place.

    Args:
        fragment: fragment to compile.
        state: current state of the compilation.
        out_circuit: circuit that will be built in-place.
        qubit_coords_map: a map associating qubit indices to their coordinates.
    """
    # If the fragment does not introduce any potential stabilizer and the previous
    # fragment did not left any stabilizers to take into account here, just add the
    # circuit of the current fragment to the main circuit and return.
    # No need to clear the state here, as it is already empty according to the
    # condition within the if branch.
    if not fragment.have_detector_sources and not state.end_stabilizers:
        out_circuit += fragment.circuit
        return
    # We gather all the potential sources (reset instructions) for the end stabilizers.
    end_stabilizer_sources = state.resets_passed_in + fragment.end_stabilizer_sources
    # construct begin stabilizers
    begin_stabilizers = _construct_boundary_stabilizers(
        sources=fragment.begin_stabilizer_sources,
        circuit=fragment.circuit,
        qubit_coords_map=qubit_coords_map,
        inverse=True,
        boundary_collapse=end_stabilizer_sources,
    )
    # form detectors
    matched_detectors = match_boundary_stabilizers(
        begin_stabilizers=begin_stabilizers,
        end_stabilizers=state.end_stabilizers,
        measurements=state.previous_measurements,
        resets=end_stabilizer_sources,
    )
    # append into circuit
    fragment_circuit_with_detectors = fragment.circuit.copy()
    for detector in sorted(matched_detectors, key=lambda d: d.coords):
        detector_inst = stim.CircuitInstruction(
            "DETECTOR",
            targets=[
                stim.target_rec(i)
                for i in sorted(detector.measurement_indices, reverse=True)
            ],
            gate_args=list(detector.coords),
        )
        fragment_circuit_with_detectors.append(detector_inst)
    if matched_detectors:
        coords_dim = max(len(d.coords) for d in matched_detectors)
        fragment_circuit_with_detectors.append(
            stim.CircuitInstruction(
                "SHIFT_COORDS", [], [0.0] * (coords_dim - 1) + [1.0]
            )
        )
    out_circuit += fragment_circuit_with_detectors
    # construct end stabilizers and update state
    state.resets_passed_in = fragment.sources_for_next_fragment
    state.previous_measurements = fragment.begin_stabilizer_sources
    state.end_stabilizers = _construct_boundary_stabilizers(
        sources=end_stabilizer_sources,
        circuit=fragment.circuit,
        qubit_coords_map=qubit_coords_map,
        inverse=False,
        boundary_collapse=fragment.begin_stabilizer_sources,
    )


def _compile_fragment_loop_into_circuit(
    fragment_loop: FragmentLoop,
    state: State,
    out_circuit: stim.Circuit,
    qubit_coords_map: dict[int, list[float]],
) -> None:
    if not fragment_loop.have_detector_sources and not state.end_stabilizers:
        body_circuit = compile_fragments_to_circuit(
            fragment_loop.fragments, qubit_coords_map
        )
        out_circuit += body_circuit * fragment_loop.repetitions
    elif fragment_loop.repetitions == 1:
        _compile_fragments_into_circuit(
            fragment_loop.fragments,
            state,
            out_circuit,
            qubit_coords_map,
        )
    else:
        # compile for the first repetition to account for
        # possible boundary effects
        first_loop_circuit = stim.Circuit()
        _compile_fragment_loop_into_circuit(
            fragment_loop.with_repetitions(1),
            state,
            first_loop_circuit,
            qubit_coords_map,
        )
        second_loop_circuit = stim.Circuit()
        _compile_fragment_loop_into_circuit(
            fragment_loop.with_repetitions(1),
            state,
            second_loop_circuit,
            qubit_coords_map,
        )
        if first_loop_circuit == second_loop_circuit:
            out_circuit += first_loop_circuit * fragment_loop.repetitions
        else:
            out_circuit += first_loop_circuit
            out_circuit += second_loop_circuit * (fragment_loop.repetitions - 1)


def _construct_boundary_stabilizers(
    sources: list[PauliString],
    circuit: stim.Circuit,
    qubit_coords_map: dict[int, list[float]],
    inverse: bool = False,
    boundary_collapse: list[PauliString] | None = None,
) -> list[BoundaryStabilizer]:
    """Compute the boundary stabilizers originating from the provided sources.

    Args:
        sources: Collapsing operations that generate propagating paulis at the circuit
            beginning (depending on the value provided to the `inverse` parameter, this
            might be the start or the end of the circuit).
        circuit: circuit considered.
        qubit_coords_map: a map associating qubit indices to their coordinates.
        inverse: Set to `True` if stabilizer propagation should be computed from the end
            to the beginning. Defaults to `False`, i.e., stabilizer propagation is
            computed in the circuit order.
        boundary_collapse: Collapsing operations at the final boundary.
            Defaults to `None` which translates to no collapsing operation.

    Returns:
        a list of stabilizers resulting from the propagation of the pauli stabilizers
        generated by `sources` through `circuit` and collapsed with `boundary_collapse`,
        in the provided `circuit` order if `inverse` is `False`, else in the reverse order.
    """
    if boundary_collapse is None:
        boundary_collapse = []

    # since the circuit is from a fragment, it's safe to ignore collapses
    circuit_tableau = circuit.to_tableau(
        ignore_noise=True, ignore_measurement=True, ignore_reset=True
    )
    if inverse:
        circuit_tableau = circuit_tableau.inverse(unsigned=True)

    stabilizers = []
    for source_index, source in enumerate(sources):
        # For each source, compute the resulting stabilizer at the other boundary.
        # 1. the stabilizers
        before_collapse = (
            source.after(circuit_tableau, targets=range(circuit.num_qubits))
            if len(circuit_tableau) > 0
            else source
        )
        after_collapse = before_collapse.collapse_by(boundary_collapse)
        # 2. the commuting and anti-commuting indices
        commute_collapse_indices = []
        anticommute_collapse_indices = []
        for i, collapse in enumerate(boundary_collapse):
            index = i - len(boundary_collapse)
            if not collapse.intersects(before_collapse):
                continue
            if before_collapse.commutes(collapse):
                commute_collapse_indices.append(index)
            else:
                anticommute_collapse_indices.append(index)
        # 3. the source measurement index
        if inverse:
            if source.weight == 0:
                source_measurement_indices = frozenset()
            else:
                source_measurement_indices = frozenset([source_index - len(sources)])
        else:
            source_measurement_indices = None
        # Append the boundary stabilizer.
        stabilizers.append(
            BoundaryStabilizer(
                before_collapse=before_collapse,
                after_collapse=after_collapse,
                commute_collapse_indices=frozenset(commute_collapse_indices),
                anticommute_collapse_indices=frozenset(anticommute_collapse_indices),
                coords=pauli_string_mean_coords(source, qubit_coords_map),
                source_measurement_indices=source_measurement_indices,
            )
        )
    return stabilizers


def match_boundary_stabilizers(
    begin_stabilizers: list[BoundaryStabilizer],
    end_stabilizers: list[BoundaryStabilizer],
    measurements: list[PauliString],
    resets: list[PauliString],
) -> list[MatchedDetector]:
    if all(bs.before_collapse.weight == 0 for bs in begin_stabilizers):
        measurements_offset = 0
    else:
        measurements_offset = len(begin_stabilizers)

    matched_detectors = []
    commute_bs = [bs for bs in begin_stabilizers if bs.all_commute]
    commute_es = [es for es in end_stabilizers if es.all_commute]
    anticommute_bs = [bs for bs in begin_stabilizers if not bs.all_commute]
    anticommute_es = [es for es in end_stabilizers if not es.all_commute]

    # 1. match stabilizers without anti-commuting collapses
    match_commute_stabilizers(
        commute_bs, commute_es, measurements_offset, matched_detectors
    )

    # 2. a set of end(begin) stabilizers that disjointedly cover the begin(end) stabilizer
    if commute_bs and commute_es:
        match_by_disjoint_cover(
            commute_bs, commute_es, measurements_offset, matched_detectors
        )
    if commute_bs and commute_es:
        match_by_disjoint_cover(
            commute_es, commute_bs, measurements_offset, matched_detectors
        )
    # 3. combine anti-commuting stabilizers
    if not ((commute_bs or anticommute_bs) and (commute_es or anticommute_es)):
        return matched_detectors
    # TODO: COMBINE ANTI-COMMUTING STABILIZERS
    return matched_detectors


def match_commute_stabilizers(
    begin_stabilizers: list[BoundaryStabilizer],
    end_stabilizers: list[BoundaryStabilizer],
    measurement_offset: int,
    detectors_out: list[MatchedDetector],
) -> None:
    for bs in list(begin_stabilizers):
        for es in list(end_stabilizers):
            if bs.after_collapse != es.after_collapse:
                continue
            detectors_out.append(
                MatchedDetector(
                    coords=bs.coords,
                    measurement_indices=frozenset(
                        bs.source_measurement_indices
                        | {i - measurement_offset for i in es.commute_collapse_indices}
                    ),
                )
            )
            begin_stabilizers.remove(bs)
            end_stabilizers.remove(es)
            break


def find_cover(
    target: BoundaryStabilizer,
    sources: list[BoundaryStabilizer],
) -> list[BoundaryStabilizer] | None:
    subsets = [
        source
        for source in sources
        if target.after_collapse.contains(source.after_collapse)
    ]
    for n in range(len(subsets), 1, -1):
        for comb in itertools.combinations(subsets, n):
            if (
                functools.reduce(
                    lambda a, b: a * b.after_collapse,
                    comb,
                    PauliString(dict()),
                )
                == target.after_collapse
            ):
                return list(comb)
            elif (
                functools.reduce(
                    lambda a, b: a * b.after_collapse, comb, target.after_collapse
                ).weight
                == 0
            ):
                return list(comb)
    return None


def match_by_disjoint_cover(
    target_stabilizers: list[BoundaryStabilizer],
    covering_stabilizers: list[BoundaryStabilizer],
    measurement_offset: int,
    detectors_out: list[MatchedDetector],
) -> None:
    for target in list(target_stabilizers):
        subsets = find_cover(target, covering_stabilizers)
        if subsets is None:
            continue
        if target.is_begin_stabilizer:
            measurement_indices = target.source_measurement_indices | frozenset(
                i - measurement_offset
                for i in functools.reduce(
                    lambda a, b: a | b.commute_collapse_indices, subsets, frozenset()
                )
            )
        else:
            measurement_indices = frozenset(
                i - measurement_offset for i in target.commute_collapse_indices
            ) | functools.reduce(
                lambda a, b: a | b.source_measurement_indices, subsets, frozenset()
            )
        detectors_out.append(
            MatchedDetector(
                coords=target.coords,
                measurement_indices=measurement_indices,
            )
        )
        target_stabilizers.remove(target)
