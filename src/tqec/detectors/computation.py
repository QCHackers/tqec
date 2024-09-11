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
    match_boundary_stabilizers,
    match_detectors_from_flows_shallow,
    match_detectors_within_fragment,
)
from tqec.circuit.operations.measurement import Measurement
from tqec.circuit.operations.operation import Detector
from tqec.exceptions import TQECException, TQECWarning
from tqec.plaquette.plaquette import Plaquettes
from tqec.position import Displacement, Position
from tqec.templates.base import Template


def _get_qubit_mapping(
    instantiation: npt.NDArray[numpy.int_],
    plaquettes_at_timestep: ty.Sequence[Plaquettes],
    increments: Displacement,
) -> dict[cirq.GridQubit, int]:
    """Get a mapping from qubit to indices for the circuit created from the
    provided `instantiation` and `plaquettes_at_timestep`.

    Args:
        instantiation: a 2-dimensional array of integers representing
            the spatial repartition of `Plaquette` instances in
            `plaquettes_at_timestep`.
        plaquettes_at_timestep: a list that contains as many values as
            there are QEC rounds in the resulting circuit. Each value
            should be a collection of `Plaquette` instances used to
            generate a quantum circuit along with `instantiation`.
        increments: spatial increments between each `Plaquette` origin.

    Raises:
        TQECException: if any qubit of the generated circuit is not a
            `cirq.GridQubit` instance.

    Returns:
        a mapping qubit -> index for all the qubits appearing in the circuit
        built from the provided `instantiation` and `plaquettes_at_timestep`.
        Each qubit should be mapped to a different index.
    """
    circuit = cirq.Circuit()
    for plaquettes in plaquettes_at_timestep:
        circuit += generate_circuit_from_instantiation(
            instantiation, plaquettes, increments
        )
    mapping: dict[cirq.GridQubit, int] = {}
    for qubit in circuit.all_qubits():
        if not isinstance(qubit, cirq.GridQubit):
            raise TQECException(
                "Found a qubit that is not an instance of cirq.GridQubit."
            )
        mapping[qubit] = len(mapping)
    return mapping


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
    # Construct the different mappings we will need during the computation
    qubit_to_index = _get_qubit_mapping(subtemplate, plaquettes_at_timestep, increments)
    index_to_qubit = {i: q for q, i in qubit_to_index.items()}
    index_to_coordinates: dict[int, tuple[float, ...]] = {
        i: (q.row, q.col) for q, i in qubit_to_index.items()
    }
    # Build one subcircuit per timestep, transform each of them into a
    # Fragment instance and build flows.
    subcircuits: list[stim.Circuit] = []
    for plaquettes in plaquettes_at_timestep:
        subcircuit = generate_circuit_from_instantiation(
            subtemplate, plaquettes, increments
        )
        subcircuits.append(
            stimcirq.cirq_circuit_to_stim_circuit(
                subcircuit,
                qubit_to_index_dict=ty.cast(dict[cirq.Qid, int], qubit_to_index),
            )
        )
    fragments = [Fragment(circ) for circ in subcircuits]
    flows = build_flows_from_fragments(fragments)
    # Match the detectors
    matched_detectors = match_detectors_within_fragment(flows[-1], index_to_coordinates)
    if len(flows) == 2:
        matched_detectors.extend(
            match_boundary_stabilizers(flows[-2], flows[-1], index_to_coordinates)
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

    filtered_detectors: list[Detector] = []
    for potential_detector in matched_detectors:
        potential_detector_measurements = {
            Measurement(index_to_qubit[m.qubit_index], m.offset)
            for m in potential_detector.measurements
        }
        if potential_detector_measurements.isdisjoint(considered_measurements):
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
            for m in potential_detector_measurements
        ]
        filtered_detectors.append(
            Detector(
                detector_measurements_central_plaquette_coordinates,
                potential_detector.coords,
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
    considered_manhattan_radius: int = 2,
) -> list[Detector]:
    plaquettes = _check_plaquettes_at_timestep(plaquettes_at_timestep)
    unique_subtemplates = template.get_spatially_distinct_subtemplates(
        considered_manhattan_radius, avoid_zero_plaquettes=True
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
