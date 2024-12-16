"""Provide functions building the :class:`~tqec.templates.rpng.RPNGTemplate`
instances representing spatial junctions."""

from typing import Literal

from tqec.compile.specs.enums import JunctionArms
from tqec.plaquette.enums import MeasurementBasis, ResetBasis
from tqec.plaquette.frozendefaultdict import FrozenDefaultDict
from tqec.plaquette.rpng import RPNGDescription
from tqec.templates.indices.qubit import QubitSpatialJunctionTemplate
from tqec.templates.rpng import RPNGTemplate


def get_spatial_junction_qubit_template(
    external_stabilizers: Literal["x", "z"],
    arms: JunctionArms,
    reset: ResetBasis | None = None,
    measurement: MeasurementBasis | None = None,
) -> RPNGTemplate:
    """Implementation of a logical qubit performing a spatial junction.

    This function returns a RPNGTemplate instance representing a logical qubit
    that is touched by 2 or more spatial junctions. The returned template is
    carefully crafted to avoid hook errors damaging the logical distance.

    Note:
        this function does not enforce anything on the input values. As such, it
        is possible to generate a description of a round that will both reset and
        measure the data-qubits.

    Arguments:
        external_stabilizers: stabilizers that are measured at each boundaries
            of the spatial junction.
        arms: flag-like enumeration listing the spatial junctions that are used
            around the logical qubit. The returned template will be adapted to
            be compatible with such a layout.
        reset: basis of the reset operation performed on data-qubits. Defaults
            to ``None`` that translates to no reset being applied on data-qubits.
        measurement: basis of the measurement operation performed on data-qubits.
            Defaults to ``None`` that translates to no measurement being applied
            on data-qubits.

    Returns:
        a description of a logical qubit performing a memory operation while
        being enclosed by 2 or more spatial junctions.
    """
    # When Python 3.10 support will be dropped:
    # assert len(arms) >= 2

    # r/m: reset/measurement basis applied to each data-qubit
    r = reset.value.lower() if reset is not None else "-"
    m = measurement.value.lower() if measurement is not None else "-"
    # be/bi = basis external/basis internal
    be = external_stabilizers
    bi = "x" if external_stabilizers == "z" else "z"

    mapping: dict[int, RPNGDescription] = {}
    # We do not care about the corners {1, 2, 3, 4} because the ones that should
    # be set will be overwritten by the junctions anyway, so there is not need
    # to set anything here.

    # Fill the boundaries that should be filled in the returned template because
    # they have no junction, and so will not be filled later.
    if JunctionArms.UP not in arms:
        mapping[10] = RPNGDescription.from_string(f"---- ---- {r}{be}3{m} {r}{be}4{m}")
    if JunctionArms.RIGHT not in arms:
        mapping[18] = RPNGDescription.from_string(f"{r}{be}1{m} ---- {r}{be}2{m} ----")
    if JunctionArms.DOWN not in arms:
        mapping[20] = RPNGDescription.from_string(f"{r}{be}1{m} {r}{be}2{m} ---- ----")
    if JunctionArms.LEFT not in arms:
        mapping[12] = RPNGDescription.from_string(f"---- {r}{be}3{m} ---- {r}{be}4{m}")

    # Assigning plaquette description to the bulk, considering that the bulk
    # corners (i.e. indices {5, 6, 7, 8}) should be assigned "regular" plaquettes
    # (i.e. 6 and 7 have the same plaquette as 17, 5 has the same plaquette as
    # 13 and 8 has the same plaquette as 15). If these need to be changed, it
    # will be done afterwards.
    internal_basis_plaquette = RPNGDescription.from_string(
        f"{r}{bi}1{m} {r}{bi}3{m} {r}{bi}2{m} {r}{bi}5{m}"
    )
    mapping[6] = internal_basis_plaquette
    mapping[7] = internal_basis_plaquette
    mapping[17] = internal_basis_plaquette

    external_basis_horizontal_hook_plaquette = RPNGDescription.from_string(
        f"{r}{be}1{m} {r}{be}2{m} {r}{be}3{m} {r}{be}4{m}"
    )
    external_basis_vertical_hook_plaquette = RPNGDescription.from_string(
        f"{r}{be}1{m} {r}{be}4{m} {r}{be}3{m} {r}{be}5{m}"
    )
    if JunctionArms.UP not in arms:
        mapping[5] = external_basis_horizontal_hook_plaquette
        mapping[13] = external_basis_horizontal_hook_plaquette
    if JunctionArms.RIGHT not in arms:
        mapping[14] = external_basis_vertical_hook_plaquette
    if JunctionArms.DOWN not in arms:
        mapping[8] = external_basis_horizontal_hook_plaquette
        mapping[15] = external_basis_horizontal_hook_plaquette
    if JunctionArms.LEFT not in arms:
        mapping[16] = external_basis_vertical_hook_plaquette

    # Last but not least, if we have a down-right or top-left L-shaped junction,
    # the corner plaquette of the bulk should be modified to measure a 3-body
    # stabilizer.
    if arms == JunctionArms.UP | JunctionArms.LEFT:
        mapping[8] = RPNGDescription.from_string(
            f"{r}{bi}1{m} {r}{bi}2{m} {r}{bi}4{m} ----"
        )
    elif arms == JunctionArms.DOWN | JunctionArms.RIGHT:
        mapping[5] = RPNGDescription.from_string(
            f"---- {r}{bi}2{m} {r}{bi}4{m} {r}{bi}5{m}"
        )

    # Sanity check: all the plaquettes in the bulk should be set.
    bulk_plaquette_indices = {5, 6, 7, 8, 13, 14, 15, 16, 17}
    missing_bulk_plaquette_indices = bulk_plaquette_indices - mapping.keys()
    assert not missing_bulk_plaquette_indices, (
        "Some plaquette(s) in the bulk were not correctly assigned to a "
        f"RPNGDescription. Missing indices: {missing_bulk_plaquette_indices}."
    )

    return RPNGTemplate(
        template=QubitSpatialJunctionTemplate(),
        mapping=FrozenDefaultDict(
            mapping,
            default_factory=lambda: RPNGDescription.from_string("---- ---- ---- ----"),
        ),
    )
