import typing as ty
import warnings

import cirq
import numpy
import numpy.typing as npt
import stim
import stimcirq

from tqec.circuit.circuit import generate_circuit_from_instantiation
from tqec.circuit.detectors.flow import build_flows_from_fragments
from tqec.circuit.detectors.fragment import Fragment
from tqec.circuit.detectors.match import (
    MatchedDetector,
    match_boundary_stabilizers,
    match_detectors_within_fragment,
)
from tqec.circuit.operations.measurement import (
    Measurement,
    get_measurements_from_circuit,
)
from tqec.circuit.operations.operation import Detector
from tqec.exceptions import TQECException, TQECWarning
from tqec.plaquette.plaquette import Plaquettes
from tqec.position import Displacement, Position
from tqec.templates.base import Template


def _get_qubit_mapping(circuit: cirq.Circuit) -> dict[cirq.GridQubit, int]:
    """Get a mapping from qubit to indices for the provided circuit.

    This function requires the whole circuit in order to avoid issues such
    as qubits only appearing in some time steps and not the others.

    Args:
        circuit: the circuit to create the mapping for.

    Raises:
        TQECException: if any qubit of the provided circuit is not a
            `cirq.GridQubit` instance.

    Returns:
        a mapping qubit -> index for all the qubits appearing in the circuit
        provided. Each qubit should be mapped to a different index.
    """
    mapping: dict[cirq.GridQubit, int] = {}
    for qubit in sorted(circuit.all_qubits()):
        if not isinstance(qubit, cirq.GridQubit):
            raise TQECException(
                "Found a qubit that is not an instance of cirq.GridQubit."
            )
        mapping[qubit] = len(mapping)
    return mapping


def _get_measurement_offset_mapping(circuit: cirq.Circuit) -> dict[int, Measurement]:
    """Get a mapping from measurement offsets as used and returned by the
    package `tqec.circuit.detectors` to a `Measurement` instance.

    This function returns the mapping from negative offsets that are
    supposed to each represent a unique measurement in the circuit to
    `Measurement` instances, that serve the same purpose but use a different
    encoding.

    Note:
        As a sanity check, the user of this function is encouraged to check
        if the qubits in each `Measurement` instances returned as values of
        the mapping corresponds to the expected qubit.

    Args:
        circuit: the circuit to create the mapping for.

    Raises:
        TQECException: if any qubit of the generated circuit is not a
            `cirq.GridQubit` instance.

    Returns:
        a mapping qubit -> index for all the qubits appearing in the circuit
        built from the provided `instantiation` and `plaquettes_at_timestep`.
        Each qubit should be mapped to a different index.
    """
    return {
        -i - 1: m
        for i, m in enumerate(reversed(get_measurements_from_circuit(circuit)))
    }


def _map_all_measurements_from_offset(
    detectors: list[MatchedDetector],
    measurements_by_offset: dict[int, Measurement],
    qubits_by_indices: dict[int, cirq.GridQubit],
) -> list[Detector]:
    ret: list[Detector] = []
    for d in detectors:
        measurements: list[Measurement] = []
        for m in d.measurements:
            measurement = measurements_by_offset[m.offset]
            expected_qubit = qubits_by_indices[m.qubit_index]
            if measurement.qubit != expected_qubit:
                raise TQECException(
                    f"Expected qubit {expected_qubit} from index {m.qubit_index} "
                    f"but got {measurement.qubit}."
                )
            measurements.append(measurement)
        ret.append(Detector(measurements, d.coords))
    return ret


def _compute_detectors_in_last_timestep_from_subtemplate(
    subtemplate: npt.NDArray[numpy.int_],
    plaquettes_at_timestep: tuple[Plaquettes] | tuple[Plaquettes, Plaquettes],
    increments: Displacement,
) -> list[Detector]:
    """Returns detectors involving measurements on the central plaquette and in
    the last timestep.

    The central plaquette of a `subtemplate` is always correctly defined as any
    `subtemplate` should have been obtained by taking a ball of a given radius `R`
    (using the Manhattan distance) around one specific plaquette. The radius `R` is
    computed from the given `subtemplate` shape.

    Args:
        subtemplate: a square 2-dimensional array of integers with odd-length
            sides representing the arrangement of plaquettes in a subtemplate.
        plaquettes_at_timestep: a tuple containing either one or two collection(s)
            of plaquettes each representing one QEC round.
        increments: spatial increments between each `Plaquette` origin.

    Returns:
        all the detectors involving at least one measurement of the central
        plaquette and from the last timestep (last values in
        `plaquettes_at_timestep`). The spatial coordinates used are all
        relative to the central plaquette origin.
    """
    radius = subtemplate.shape[0] // 2
    # Build subcircuit for each Plaquettes layer
    subcircuits_cirq: list[cirq.Circuit] = []
    complete_circuit_cirq = cirq.Circuit()
    for plaquettes in plaquettes_at_timestep:
        subcircuit_cirq = generate_circuit_from_instantiation(
            subtemplate, plaquettes, increments
        )
        complete_circuit_cirq += subcircuit_cirq
        subcircuits_cirq.append(subcircuit_cirq)

    # Construct the different mappings we will need during the computation
    indices_by_qubit = _get_qubit_mapping(complete_circuit_cirq)
    qubits_by_index = {i: q for q, i in indices_by_qubit.items()}
    coordinates_by_index: dict[int, tuple[float, ...]] = {
        i: (q.row, q.col) for q, i in indices_by_qubit.items()
    }
    measurements_by_offset = _get_measurement_offset_mapping(complete_circuit_cirq)

    subcircuits_stim: list[stim.Circuit] = [
        stimcirq.cirq_circuit_to_stim_circuit(
            subcircuit_cirq,
            qubit_to_index_dict=ty.cast(dict[cirq.Qid, int], indices_by_qubit),
        )
        for subcircuit_cirq in subcircuits_cirq
    ]

    fragments = [Fragment(circ) for circ in subcircuits_stim]
    flows = build_flows_from_fragments(fragments)
    # Match the detectors
    matched_detectors = match_detectors_within_fragment(flows[-1], coordinates_by_index)
    if len(flows) == 2:
        matched_detectors.extend(
            match_boundary_stabilizers(flows[-2], flows[-1], coordinates_by_index)
        )
    potential_detectors = _map_all_measurements_from_offset(
        matched_detectors, measurements_by_offset, qubits_by_index
    )

    # Compute the coordinates of the measurements we care about (i.e., only the
    # measurements from the central plaquette).
    central_plaquette_index: int = subtemplate[radius, radius]
    central_plaquette = plaquettes_at_timestep[-1][central_plaquette_index]
    # considered_measurements is using the subtemplate coordinate system (origin is
    # at the top-left corner of the subtemplate).
    considered_measurements = {
        m.offset_spatially_by(radius * increments.x, radius * increments.y)
        for m in central_plaquette.measurements
    }
    if not considered_measurements:
        return []

    filtered_detectors: list[Detector] = []
    for potential_detector in potential_detectors:
        if not considered_measurements.issubset(potential_detector.measurement_data):
            # This is not an interesting detector, filter it out.
            continue
        # From here on, potential_detector is a detector we want to keep.
        # We have two transformations to apply to it:
        # 1. Change of coordinate system for the qubits. potential_detector is
        #    using a coordinate system with the origin at the top-left corner of
        #    the current sub-template, but we need to return detectors that use
        #    the central plaquette origin as their coordinate system origin.
        # 2. Transform the MatchedDetector instance into a Detector instance.
        detector_measurements_central_plaquette_coordinates = [
            m.offset_spatially_by(-radius * increments.x, -radius * increments.y)
            for m in potential_detector.measurement_data
        ]
        filtered_detectors.append(
            Detector(
                detector_measurements_central_plaquette_coordinates,
                potential_detector.coordinates,
            )
        )
    return filtered_detectors


def _check_plaquettes_at_timestep(
    plaquettes_at_timestep: list[Plaquettes],
) -> tuple[Plaquettes] | tuple[Plaquettes, Plaquettes]:
    if len(plaquettes_at_timestep) == 0:
        raise TQECException(
            "Cannot compute detectors without plaquettes to build a circuit."
        )
    if len(plaquettes_at_timestep) == 1:
        return (plaquettes_at_timestep[0],)
    if len(plaquettes_at_timestep) > 2:
        warnings.warn(
            "Detector computation is currently limited to flows from 2 "
            f"adjacent QEC rounds. You provided {len(plaquettes_at_timestep)} "
            "QEC rounds. Only the last 2 rounds will be considered.",
            TQECWarning,
        )
    return plaquettes_at_timestep[0], plaquettes_at_timestep[1]


def compute_detectors_in_last_timestep(
    template: Template,
    plaquettes_at_timestep: list[Plaquettes],
    fixed_subtemplate_radius: int = 2,
) -> list[Detector]:
    plaquettes = _check_plaquettes_at_timestep(plaquettes_at_timestep)
    unique_subtemplates = template.get_spatially_distinct_subtemplates(
        fixed_subtemplate_radius, avoid_zero_plaquettes=True
    )
    increments = template.get_increments()
    # Each detector in detectors_by_subtemplate is using a coordinate system
    # centered on the central plaquette origin.
    detectors_by_subtemplate: dict[int, list[Detector]] = {
        i: _compute_detectors_in_last_timestep_from_subtemplate(
            subtemplate, plaquettes, increments
        )
        for i, subtemplate in unique_subtemplates.subtemplates.items()
    }

    detectors: list[Detector] = []
    for i, row in enumerate(unique_subtemplates.subtemplate_indices):
        for j, subtemplate_index in enumerate(row):
            plaquette_origin = Position(j * increments.x, i * increments.x)
            for d in detectors_by_subtemplate[subtemplate_index]:
                offset_measurements = [
                    m.offset_spatially_by(plaquette_origin.x, plaquette_origin.y)
                    for m in d.measurement_data
                ]
                detectors.append(Detector(offset_measurements, d.coordinates))
    return detectors
