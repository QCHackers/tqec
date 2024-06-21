from __future__ import annotations

import stim
from tqec.circuit.detectors.flow import build_flows_from_fragments
from tqec.circuit.detectors.fragment import (
    Fragment,
    FragmentLoop,
    split_stim_circuit_into_fragments,
)
from tqec.circuit.detectors.match import (
    MatchedDetector,
    match_detectors_from_flows_shallow,
)


def _detectors_to_circuit(
    detectors: list[MatchedDetector], additional_coordinates: list[float] | None = None
) -> stim.Circuit:
    """Transform a list of detectors into a circuit.

    Args:
        detectors: detectors that will be included in the returned circuit.

    Returns:
        A `stim.Circuit` instance containing all the provided detectors.
    """
    if additional_coordinates is None:
        additional_coordinates = []

    circuit = stim.Circuit()

    for detector in detectors:
        circuit.append(detector.to_instruction())

    return circuit


def _shift_time_instruction(number_of_spatial_coordinates: int) -> stim.Circuit:
    args = tuple(0.0 for _ in range(number_of_spatial_coordinates)) + (1.0,)
    circuit = stim.Circuit()
    circuit.append(
        stim.CircuitInstruction("SHIFT_COORDS", targets=[], gate_args=list(args))
    )
    return circuit


def annotate_detectors_automatically(circuit: stim.Circuit) -> stim.Circuit:
    """Insert detectors into the provided circuit instance.

    This is the main user-facing function to automatically insert detectors into
    a quantum circuit composed of Clifford operations. The provided circuit should
    check some pre-conditions to be accepted, which are detailled in details below.

    First and foremost, the provided circuit should check the pre-conditions listed
    in the documentation of :func:`split_stim_circuit_into_fragments`.

    Args:
        circuit: circuit to insert detectors in.

    Returns:
        A new `stim.Circuit` instance with automatically computed detectors.
    """
    fragments = split_stim_circuit_into_fragments(circuit)
    qubit_coords_map = {
        q: tuple(coords) for q, coords in circuit.get_final_qubit_coordinates().items()
    }
    return compile_fragments_to_circuit_with_detectors(fragments, qubit_coords_map)


def compile_fragments_to_circuit(
    fragments: list[Fragment | FragmentLoop],
) -> stim.Circuit:
    circuit = stim.Circuit()

    for fragment in fragments:
        if isinstance(fragment, Fragment):
            circuit += fragment.circuit
        else:  # isinstance(fragment, FragmentLoop):
            loop_body = compile_fragments_to_circuit(fragment.fragments)
            circuit += loop_body * fragment.repetitions
    return circuit


def _tick_circuit() -> stim.Circuit:
    return stim.Circuit("TICK")


def _remove_last_tick_instruction(circuit: stim.Circuit) -> stim.Circuit:
    if circuit[-1].name == "TICK":
        return circuit[:-1]
    return circuit


def compile_fragments_to_circuit_with_detectors(
    fragments: list[Fragment | FragmentLoop],
    qubit_coords_map: dict[int, tuple[float, ...]],
) -> stim.Circuit:
    flows = build_flows_from_fragments(fragments)
    detectors_from_flows = match_detectors_from_flows_shallow(flows, qubit_coords_map)

    circuit = stim.Circuit()

    for fragment, detectors in zip(fragments, detectors_from_flows):
        detectors_circuit = _detectors_to_circuit(detectors, [0.0])
        if isinstance(fragment, Fragment):
            circuit += (
                _remove_last_tick_instruction(fragment.circuit)
                + detectors_circuit
                + _tick_circuit()
            )
        else:  # isinstance(fragment, FragmentLoop):
            shift_circuit = _shift_time_instruction(len(detectors[0].coords) - 1)
            loop_body = compile_fragments_to_circuit_with_detectors(
                fragment.fragments, qubit_coords_map
            )
            circuit += (
                _remove_last_tick_instruction(loop_body)
                + shift_circuit
                + detectors_circuit
                + _tick_circuit()
            ) * fragment.repetitions
    return circuit
