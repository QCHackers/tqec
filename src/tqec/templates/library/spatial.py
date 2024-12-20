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

    Warning:
        by convention, this function does not populate the plaquettes on the
        boundaries where an arm (i.e. spatial junction) is present **BUT** do
        populate the corners (that are part of the boundaries, so this is an
        exception to the sentence just before).

        Junctions should follow that convention and should not replace the
        plaquette descriptions on the corners.

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
    # In this function implementation, all the indices used are referring to the
    # indices returned by the QubitSpatialJunctionTemplate template. They are
    # copied below for convenience, but the only source of truth is in the
    # QubitSpatialJunctionTemplate docstring!
    #      1   9  10   9  10   9  10   9  10   2
    #     11   5  17  13  17  13  17  13   6  18
    #     12  17  13  17  13  17  13  17  14  19
    #     11  16  17  13  17  13  17  14  17  18
    #     12  17  16  17  13  17  14  17  14  19
    #     11  16  17  16  17  15  17  14  17  18
    #     12  17  16  17  15  17  15  17  14  19
    #     11  16  17  15  17  15  17  15  17  18
    #     12   7  15  17  15  17  15  17   8  19
    #      3  20  21  20  21  20  21  20  21   4

    # When Python 3.10 support will be dropped:
    # assert len(arms) >= 2

    # r/m: reset/measurement basis applied to each data-qubit
    r = reset.value.lower() if reset is not None else "-"
    m = measurement.value.lower() if measurement is not None else "-"
    # be/bi = basis external/basis internal
    be = external_stabilizers
    bi = "x" if external_stabilizers == "z" else "z"

    mapping: dict[int, RPNGDescription] = {}
    ####################
    #     Corners      #
    ####################
    # Corners 2 and 3 are always empty, but corners 1 and 4 might contain a 3-body
    # stabilizer measurement if both arms around are set.
    if JunctionArms.UP in arms and JunctionArms.LEFT in arms:
        mapping[1] = RPNGDescription.from_string(
            f"---- {r}{be}2{m} {r}{be}4{m} {r}{be}5{m}"
        )
    if JunctionArms.DOWN in arms and JunctionArms.RIGHT in arms:
        mapping[4] = RPNGDescription.from_string(
            f"{r}{be}1{m} {r}{be}2{m} {r}{be}4{m} ----"
        )

    ####################
    #    Boundaries    #
    ####################
    # Fill the boundaries that should be filled in the returned template because
    # they have no junction, and so will not be filled later.
    # Note that indices 1 and 4 **might** be set twice in the 4 ifs below. These
    # cases are handled later in the function and will overwrite the description
    # on 1 and 4 if needed, so we do not have to account for those cases here.
    if JunctionArms.UP not in arms:
        mapping[1] = RPNGDescription.from_string(f"---- ---- {r}{be}3{m} {r}{be}4{m}")
        mapping[10] = RPNGDescription.from_string(f"---- ---- {r}{be}3{m} {r}{be}4{m}")
    if JunctionArms.RIGHT not in arms:
        mapping[4] = RPNGDescription.from_string(f"{r}{be}1{m} ---- {r}{be}2{m} ----")
        mapping[18] = RPNGDescription.from_string(f"{r}{be}1{m} ---- {r}{be}2{m} ----")
    if JunctionArms.DOWN not in arms:
        mapping[4] = RPNGDescription.from_string(f"{r}{be}1{m} {r}{be}2{m} ---- ----")
        mapping[20] = RPNGDescription.from_string(f"{r}{be}1{m} {r}{be}2{m} ---- ----")
    if JunctionArms.LEFT not in arms:
        mapping[1] = RPNGDescription.from_string(f"---- {r}{be}3{m} ---- {r}{be}4{m}")
        mapping[12] = RPNGDescription.from_string(f"---- {r}{be}3{m} ---- {r}{be}4{m}")

    # If we have a down-right or top-left L-shaped junction, the opposite corner
    # plaquette should be removed from the mapping (this is the case where it
    # has been set twice in the ifs above).
    if arms == JunctionArms.UP | JunctionArms.LEFT:
        del mapping[4]
    elif arms == JunctionArms.DOWN | JunctionArms.RIGHT:
        del mapping[1]

    ####################
    #       Bulk       #
    ####################
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

    # be{h,v}hp: basis external {horizontal,vertical} hook plaquette
    behhp = RPNGDescription.from_string(
        f"{r}{be}1{m} {r}{be}2{m} {r}{be}3{m} {r}{be}4{m}"
    )
    bevhp = RPNGDescription.from_string(
        f"{r}{be}1{m} {r}{be}4{m} {r}{be}3{m} {r}{be}5{m}"
    )
    mapping[5] = bevhp if JunctionArms.UP in arms else behhp
    mapping[13] = bevhp if JunctionArms.UP in arms else behhp
    mapping[14] = behhp if JunctionArms.RIGHT in arms else bevhp
    mapping[8] = bevhp if JunctionArms.DOWN in arms else behhp
    mapping[15] = bevhp if JunctionArms.DOWN in arms else behhp
    mapping[16] = behhp if JunctionArms.LEFT in arms else bevhp

    # In the special cases of an L-shaped junction TOP/LEFT or DOWN/RIGHT, the
    # opposite corner **within the bulk** should be overwritten to become a
    # 3-body stabilizer measurement.
    if arms == JunctionArms.UP | JunctionArms.LEFT:
        mapping[8] = RPNGDescription.from_string(
            f"{r}{be}1{m} {r}{be}2{m} {r}{be}4{m} ----"
        )
    elif arms == JunctionArms.DOWN | JunctionArms.RIGHT:
        mapping[5] = RPNGDescription.from_string(
            f"---- {r}{be}2{m} {r}{be}4{m} {r}{be}5{m}"
        )

    ####################
    #  Sanity checks   #
    ####################
    # All the plaquettes in the bulk should be set.
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
