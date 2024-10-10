import stim

from tqec.circuit.detectors.flow import build_flows_from_fragments
from tqec.circuit.detectors.fragment import Fragment
from tqec.circuit.detectors.match import (
    MatchedDetector,
    match_boundary_stabilizers,
    match_detectors_within_fragment,
)
from tqec.circuit.generation import generate_circuit_from_instantiation
from tqec.circuit.measurement import Measurement, get_measurements_from_circuit
from tqec.circuit.qubit import GridQubit
from tqec.circuit.schedule import ScheduledCircuit, relabel_circuits_qubit_indices
from tqec.compile.detectors.database import DetectorDatabase
from tqec.compile.detectors.detector import Detector
from tqec.exceptions import TQECException
from tqec.plaquette.plaquette import Plaquettes
from tqec.position import Displacement, Position2D
from tqec.templates.base import Template
from tqec.templates.subtemplates import SubTemplateType


def _get_measurement_offset_mapping(circuit: stim.Circuit) -> dict[int, Measurement]:
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


def _matched_detectors_to_detectors(
    detectors: list[MatchedDetector],
    measurements_by_offset: dict[int, Measurement],
    qubits_by_indices: dict[int, GridQubit],
) -> frozenset[Detector]:
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
        ret.append(Detector(frozenset(measurements), d.coords))
    return frozenset(ret)


def _compute_detectors_at_end_of_situation(
    subtemplates: tuple[SubTemplateType] | tuple[SubTemplateType, SubTemplateType],
    plaquettes_by_timestep: tuple[Plaquettes] | tuple[Plaquettes, Plaquettes],
    increments: Displacement,
) -> frozenset[Detector]:
    # Build subcircuit for each Plaquettes layer
    subcircuits: list[ScheduledCircuit] = []
    for subtemplate, plaquettes in zip(subtemplates, plaquettes_by_timestep):
        subcircuit = generate_circuit_from_instantiation(
            subtemplate, plaquettes, increments
        )
        subcircuits.append(subcircuit)

    # Extract the global qubit map from the generated sub-circuits, relabeling
    # qubits if needed.
    subcircuits, global_qubit_map = relabel_circuits_qubit_indices(subcircuits)
    # Get the stim.Circuit instances. We do not need the coordinates here
    # because we have already computed the global qubit map.
    coordless_subcircuits = [
        sc.get_circuit(include_qubit_coords=False) for sc in subcircuits
    ]
    complete_circuit = global_qubit_map.to_circuit() + sum(
        coordless_subcircuits, start=stim.Circuit()
    )
    # Construct the different mappings we will need during the computation
    measurements_by_offset = _get_measurement_offset_mapping(complete_circuit)
    coordinates_by_index = {
        i: (float(q.x), float(q.y)) for i, q in global_qubit_map.items()
    }
    # Start the detector computation.
    fragments = [Fragment(circ) for circ in coordless_subcircuits]
    flows = build_flows_from_fragments(fragments)
    # Match the detectors
    matched_detectors = match_detectors_within_fragment(flows[-1], coordinates_by_index)
    if len(flows) == 2:
        matched_detectors.extend(
            match_boundary_stabilizers(flows[-2], flows[-1], coordinates_by_index)
        )

    return _matched_detectors_to_detectors(
        matched_detectors, measurements_by_offset, global_qubit_map.i2q
    )


def compute_detectors_at_end_of_situation(
    subtemplates: tuple[SubTemplateType] | tuple[SubTemplateType, SubTemplateType],
    plaquettes_by_timestep: tuple[Plaquettes] | tuple[Plaquettes, Plaquettes],
    increments: Displacement,
    database: DetectorDatabase | None = None,
) -> frozenset[Detector]:
    """Returns detectors that should be added at the end of the provided situation.

    Args:
        subtemplates: a tuple containing either one or two sub-template(s), each
            consisting of square 2-dimensional array of integers with odd-length
            sides representing the arrangement of plaquettes in a subtemplate.
        plaquettes_at_timestep: a tuple containing either one or two collection(s)
            of plaquettes each representing one QEC round.
        increments: spatial increments between each `Plaquette` origin.
        database: existing database of detectors that is used to avoid computing
            detectors if the database already contains them. If provided, this
            function guarantees that the database will contain the provided
            situation when returning (i.e., either it already contained the
            situation or it has been updated **in-place** with the computed
            detectors). Default to `None` which result in not using any kind of
            database and unconditionally performing the detector computation.

    Returns:
        all the detectors that can be appended at the end of the circuit
        represented by the provided `subtemplates` and `plaquettes_at_timestep`.

    Raises:
        TQECException: if `len(subtemplates) != len(plaquettes_at_timestep)`.
    """
    if len(subtemplates) != len(plaquettes_by_timestep):
        raise TQECException("You should provide as many subtemplates as timesteps.")

    # Try to recover the result from the database.
    if database is not None:
        detectors = database.get_detectors(subtemplates, plaquettes_by_timestep)
        # If not found, compute and store in database.
        if detectors is None:
            detectors = _compute_detectors_at_end_of_situation(
                subtemplates, plaquettes_by_timestep, increments
            )
            database.add_situation(subtemplates, plaquettes_by_timestep, detectors)
    # If database is None, just compute the detectors.
    else:
        detectors = _compute_detectors_at_end_of_situation(
            subtemplates, plaquettes_by_timestep, increments
        )

    # `subtemplate.shape` should be `(2 * radius + 1, 2 * radius + 1)` so we can
    # recover the radius with the below expression.
    radius = subtemplates[0].shape[0] // 2

    # We have a coordinate system change to apply to `detectors`.
    # `detectors` is using a coordinate system with the origin at the
    # top-left corner of the current sub-template, but we need to return
    # detectors that use the central plaquette origin as their coordinate system
    # origin.
    shift_x, shift_y = -radius * increments.x, -radius * increments.y

    return frozenset(d.offset_spatially_by(shift_x, shift_y) for d in detectors)


def compute_detectors_for_constant_template_and_fixed_radius(
    template: Template,
    k: int,
    plaquettes_at_timestep: tuple[Plaquettes] | tuple[Plaquettes, Plaquettes],
    fixed_subtemplate_radius: int = 2,
    database: DetectorDatabase | None = None,
) -> frozenset[Detector]:
    """Returns detectors that should be added at the end of the circuit that would
    be obtained from the provided `template` and `plaquettes_at_timestep`.

    Args:
        template: constant Template that describes accurately the plaquette
            arrangement on all the considered timesteps.
        k: scaling factor to consider in order to instantiate the provided
            template.
        plaquettes_at_timestep: a tuple containing either one or two collection(s)
            of plaquettes each representing one QEC round.
        fixed_subtemplate_radius: Manhattan radius to consider when splitting the
            provided `template` into sub-templates. Should be large enough so
            that flows cancelling each other to form a detector are strictly
            contained in the sub-template and cannot escape from it (which is
            mostly equivalent to say that flows should not interact with qubits
            on the border of the sub-templates).
        database: existing database of detectors that is used to avoid computing
            detectors if the database already contains them. If provided, this
            function guarantees that the database will contain the provided
            situation when returning (i.e., either it already contained the
            situation or it has been updated **in-place** with the computed
            detectors). Default to `None` which result in not using any kind of
            database and unconditionally performing the detector computation.

    Returns:
        a collection of detectors that should be added at the end of the circuit
        that would be obtained from the provided `template` and
        `plaquettes_at_timestep`.
    """
    unique_subtemplates = template.get_spatially_distinct_subtemplates(
        k, fixed_subtemplate_radius, avoid_zero_plaquettes=True
    )
    increments = template.get_increments()
    # Each detector in detectors_by_subtemplate is using a coordinate system
    # centered on the central plaquette origin.
    detectors_by_subtemplate: dict[int, frozenset[Detector]] = {
        i: compute_detectors_at_end_of_situation(
            (subtemplate,)
            if len(plaquettes_at_timestep) == 1
            else (subtemplate, subtemplate),
            plaquettes_at_timestep,
            increments,
            database,
        )
        for i, subtemplate in unique_subtemplates.subtemplates.items()
    }

    detectors_by_measurements: dict[frozenset[Measurement], Detector] = dict()
    for i, row in enumerate(unique_subtemplates.subtemplate_indices):
        for j, subtemplate_index in enumerate(row):
            if subtemplate_index == 0:
                continue
            plaquette_origin = Position2D(j * increments.x, i * increments.y)
            for d in detectors_by_subtemplate[subtemplate_index]:
                offset_measurements = frozenset(
                    m.offset_spatially_by(plaquette_origin.x, plaquette_origin.y)
                    for m in d.measurements
                )
                # We use the convention of `cirq.GridQubit` where the first coordinate
                # is the column and the second coordinate is the row. Note that the
                # coordinates of detectors are derived from the qubits, which are
                # already in the `GridQubit` convention. So we only need to swap the
                # coordinates of the plaquette origin.
                coordinates = (
                    d.coordinates[0] + plaquette_origin.y,
                    d.coordinates[1] + plaquette_origin.x,
                    *d.coordinates[2:],
                )
                detectors_by_measurements[frozenset(offset_measurements)] = Detector(
                    offset_measurements, coordinates
                )
    return frozenset(detectors_by_measurements.values())
