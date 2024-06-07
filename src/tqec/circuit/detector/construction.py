from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import stim
from tqec.circuit.detector.fragment import (
    Fragment,
    FragmentLoop,
    split_stim_circuit_into_fragments,
)
from tqec.circuit.detector.match import match_boundary_stabilizers
from tqec.circuit.detector.pauli import PauliString
from tqec.circuit.detector.stabilizer import BoundaryStabilizer
from tqec.circuit.detector.utils import pauli_string_mean_coords


def annotate_detectors_automatically(circuit: stim.Circuit) -> stim.Circuit:
    fragments = split_stim_circuit_into_fragments(circuit)
    return compile_fragments_to_circuit(
        fragments, qubit_coords_map=circuit.get_final_qubit_coordinates()
    )


@dataclass
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
    """Compile the provided fragment into the provided circuit.

    Warning:
        This function **mutates** its parameters in-place.

    Args:
        fragment_loop: fragment to compile.
        state: current state of the compilation.
        out_circuit: circuit that will be built in-place.
        qubit_coords_map: a map associating qubit indices to their coordinates.
    """
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
        # 3. If the inverse parameter is True, the source is a measurement instruction.
        #    If that is the case, we want to save that information for later as we will
        #    need a way to recover information on this measurement to include it in the
        #    detectors.
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
