import numpy
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
from tqec.plaquette.enums import PlaquetteSide
from tqec.plaquette.plaquette import Plaquettes
from tqec.position import Displacement
from tqec.templates.base import Template
from tqec.templates.subtemplates import (
    SubTemplateType,
    get_spatially_distinct_3d_subtemplates,
)


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

    Returns:
        a mapping from record offset to :class:`Measurement` for all the
        measurements appearing in the provided `circuit`.
    """
    return {
        -i - 1: m
        for i, m in enumerate(reversed(get_measurements_from_circuit(circuit)))
    }


def _matched_detectors_to_detectors(
    detectors: list[MatchedDetector],
    measurements_by_offset: dict[int, Measurement],
    qubits_by_indices: dict[int, GridQubit],
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
        ret.append(Detector(frozenset(measurements), d.coords))
    return ret


def _center_plaquette_syndrome_qubits(
    subtemplate: SubTemplateType, plaquettes: Plaquettes, increments: Displacement
) -> list[GridQubit]:
    """Return a collection of qubits that are used as syndrome qubits by the central
    plaquette of the provided `subtemplate`.

    The qubits are returned in the sub-template coordinates (i.e., origin at
    top-left corner of the provided `subtemplate`).

    Args:
        subtemplate: 2-dimensional array representing the sub-template we are
            interested in.
        plaquettes: a collection of plaquettes that will be used to generate a
            circuit from the provided `subtemplate`.
        increments: spatial increments between each `Plaquette` origin.

    Returns:
        a collection of qubits that are used as syndrome qubits by the central
        plaquette. Returns an empty collection if the central plaquette has the
        index `0`.
    """
    r = subtemplate.shape[0] // 2
    central_plaquette_index = int(subtemplate[r, r])

    if central_plaquette_index == 0:
        return []

    central_plaquette = plaquettes[central_plaquette_index]
    origin = central_plaquette.origin
    offset = Displacement(r * increments.x + origin.x, r * increments.y + origin.y)
    return [q + offset for q in central_plaquette.qubits.syndrome_qubits]


def _filter_detectors(
    detectors: list[Detector],
    subtemplates: tuple[SubTemplateType] | tuple[SubTemplateType, SubTemplateType],
    plaquettes: tuple[Plaquettes] | tuple[Plaquettes, Plaquettes],
    increments: Displacement,
) -> frozenset[Detector]:
    # First, we want the detectors to be composed of at least one measurement
    # involving one of the syndrome qubits of the central plaquette in the last
    # timestep.
    central_syndrome_qubits_measurements = frozenset(
        # Assumes that syndrome qubits are only measured once per round, which
        # seems reasonable. But still, this is an important assumption.
        Measurement(q, -1)
        for q in _center_plaquette_syndrome_qubits(
            subtemplates[-1], plaquettes[-1], increments
        )
    )
    filtered_detectors = [
        d
        for d in detectors
        if d.measurements.intersection(central_syndrome_qubits_measurements)
    ]
    return frozenset(filtered_detectors)


def _compute_detectors_at_end_of_situation(
    subtemplates: tuple[SubTemplateType] | tuple[SubTemplateType, SubTemplateType],
    plaquettes: tuple[Plaquettes] | tuple[Plaquettes, Plaquettes],
    increments: Displacement,
) -> frozenset[Detector]:
    if len(plaquettes) != len(subtemplates):
        raise TQECException(
            "Unsupported input: you should provide as many subtemplates as "
            "there are plaquettes."
        )
    # Note: if the last entry of `subtemplates` is full of zero, then we can be
    #       sure there are no detectors here, so early return.
    if numpy.all(subtemplates[-1] == 0):
        return frozenset()

    # Note: if `len(subtemplates) == 2`, the first entry might be full of zeros.
    #       In this case, just consider the second entry.
    if len(subtemplates) == 2 and numpy.all(subtemplates[0] == 0):
        assert len(plaquettes) == 2  # make type checkers happy
        subtemplates = (subtemplates[1],)
        plaquettes = (plaquettes[1],)

    # Build subcircuit for each Plaquettes layer
    subcircuits: list[ScheduledCircuit] = []
    for subtemplate, plaqs in zip(subtemplates, plaquettes):
        subcircuit = generate_circuit_from_instantiation(subtemplate, plaqs, increments)
        subcircuits.append(subcircuit)
    # Extract the global qubit map from the generated sub-circuits, relabeling
    # qubits if needed.
    subcircuits, global_qubit_map = relabel_circuits_qubit_indices(subcircuits)
    # Get the stim.Circuit instances. We do not need the coordinates here
    # because we have already computed the global qubit map.
    coordless_subcircuits = [
        sc.get_circuit(include_qubit_coords=False) for sc in subcircuits
    ]
    # Get the full stim.Circuit to compute a measurement records offset map and
    # filter out detectors at the end.
    complete_circuit = global_qubit_map.to_circuit()
    for coordless_subcircuit in coordless_subcircuits[:-1]:
        complete_circuit += coordless_subcircuit
        complete_circuit.append("TICK", [], [])
    complete_circuit += coordless_subcircuits[-1]

    # Use tqec.circuit.detectors module to match the detectors.
    coordinates_by_index = {
        i: (float(q.x), float(q.y)) for i, q in global_qubit_map.items()
    }
    fragments = [Fragment(circ) for circ in coordless_subcircuits]
    flows = build_flows_from_fragments(fragments)
    matched_detectors = match_detectors_within_fragment(flows[-1], coordinates_by_index)
    if len(flows) == 2:
        matched_detectors.extend(
            match_boundary_stabilizers(flows[-2], flows[-1], coordinates_by_index)
        )

    # Get the detectors as Detector instances instead of the
    # `tqec.circuit.detectors.MatchedDetector` class.
    measurements_by_offset = _get_measurement_offset_mapping(complete_circuit)
    detectors = _matched_detectors_to_detectors(
        matched_detectors, measurements_by_offset, global_qubit_map.i2q
    )

    # Filter out detectors and return the left ones.
    return _filter_detectors(detectors, subtemplates, plaquettes, increments)


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


def compute_detectors_for_fixed_radius(
    template_at_timestep: tuple[Template] | tuple[Template, Template],
    k: int,
    plaquettes_at_timestep: tuple[Plaquettes] | tuple[Plaquettes, Plaquettes],
    fixed_subtemplate_radius: int = 2,
    database: DetectorDatabase | None = None,
) -> list[Detector]:
    """Returns detectors that should be added at the end of the circuit that would
    be obtained from the provided `template_at_timestep` and
    `plaquettes_at_timestep`.

    Args:
        template_at_timestep: a tuple containing either one or two :class:`Template`
            instance(s), each representing one QEC round.
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
        that would be obtained from the provided `template_at_timestep` and
        `plaquettes_at_timestep`.
    """
    all_increments = frozenset(t.get_increments() for t in template_at_timestep)
    if len(all_increments) != 1:
        raise TQECException(
            "Expected all the provided templates to have the same increments. "
            f"Found the following different increments: {all_increments}."
        )
    increments = next(iter(all_increments))

    unique_3d_subtemplates = get_spatially_distinct_3d_subtemplates(
        tuple(t.instantiate(k) for t in template_at_timestep),
        manhattan_radius=fixed_subtemplate_radius,
        avoid_zero_plaquettes=True,
    )

    # Each detector in detectors_by_subtemplate is using a coordinate system
    # centered on the central plaquette origin.
    detectors_by_subtemplate: dict[tuple[int, ...], frozenset[Detector]] = {
        indices: compute_detectors_at_end_of_situation(
            (s3d[:, :, 0], s3d[:, :, 1]),
            plaquettes_at_timestep,
            increments,
            database,
        )
        for indices, s3d in unique_3d_subtemplates.subtemplates.items()
    }
    # We know for sure that detectors in each subtemplate all involve a measurement
    # on at least one syndrome qubit of the central plaquette. That means that
    # detectors computed here are unique and we do not have to check for
    # duplicates.
    detectors: list[Detector] = []
    for i, row in enumerate(unique_3d_subtemplates.subtemplate_indices):
        for j, subtemplate_indices in enumerate(row):
            if numpy.all(subtemplate_indices == 0):
                continue
            for d in detectors_by_subtemplate[tuple(subtemplate_indices)]:
                detectors.append(
                    d.offset_spatially_by(j * increments.x, i * increments.y)
                )

    return detectors
