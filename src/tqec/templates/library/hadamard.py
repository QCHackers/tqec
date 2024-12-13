from typing import Literal

from tqec.plaquette.frozendefaultdict import FrozenDefaultDict
from tqec.plaquette.rpng import RPNGDescription
from tqec.templates.enums import ZObservableOrientation
from tqec.templates.indices.qubit import QubitTemplate, QubitVerticalBorders
from tqec.templates.rpng import RPNGTemplate


def get_temporal_hadamard_template(
    orientation: ZObservableOrientation = ZObservableOrientation.HORIZONTAL,
) -> RPNGTemplate:
    """Returns a representation of a transversal Hadamard gate applied on one
    logical qubit.

    This function returns a RPNGTemplate instance that performs a transversal
    Hadamard gate. It is basically performing a standard memory operation, but
    also include a Hadamard gate on each data-qubit, effectively performing a
    fault-tolerant Hadamard gate by transversal application of physical gates.

    Arguments:
        orientation: orientation of the Z observable. Used to compute the
            stabilizers that should be measured on the boundaries and in the
            bulk of the returned logical qubit description.

    Returns:
        an implementation of transversal Hadamard gate.
    """
    bh: Literal["x", "z"]
    bv: Literal["x", "z"]
    if orientation == ZObservableOrientation.HORIZONTAL:
        bh, bv = "z", "x"
    else:
        bh, bv = "x", "z"

    return RPNGTemplate(
        template=QubitTemplate(),
        mapping=FrozenDefaultDict(
            {
                # XX_UP
                6: RPNGDescription.from_string(f"---- ---- -{bv}3h -{bv}4h"),
                # ZZ_LEFT
                7: RPNGDescription.from_string(f"---- -{bh}3h ---- -{bh}4h"),
                # XXXX
                9: RPNGDescription.from_string(f"-{bv}1h -{bv}2h -{bv}3h -{bv}4h"),
                # ZZZZ
                10: RPNGDescription.from_string(f"-{bh}1h -{bh}3h -{bh}2h -{bh}4h"),
                # ZZ_RIGHT
                12: RPNGDescription.from_string(f"-{bh}1h ---- -{bh}2h ----"),
                # XX_DOWN
                13: RPNGDescription.from_string(f"-{bv}1h -{bv}2h ---- ----"),
            },
            default_factory=lambda: RPNGDescription.from_string("---- ---- ---- ----"),
        ),
    )


def get_spatial_horizontal_hadamard_template(
    top_left_is_z_stabilizer: bool,
) -> RPNGTemplate:
    """Returns a representation of a "transversal" Hadamard gate at the interface
    between two logical qubits.

    Note:
        by convention, the hadamard-like transition is performed at the top-most
        plaquettes.

    Arguments:
        top_left_is_z_stabilizer: if ``True``, the top-left physical qubit should
            be measuring a Z stabilizer. Else, it measures a X stabilizer.
    """
    raise NotImplementedError()


def get_spatial_vertical_hadamard_template(
    top_left_is_z_stabilizer: bool,
) -> RPNGTemplate:
    """Returns a representation of a "transversal" Hadamard gate at the interface
    between two logical qubits.

    Note:
        by convention, the hadamard-like transition is performed at the left-most
        plaquettes.

    Arguments:
        top_left_is_z_stabilizer: if ``True``, the top-left physical qubit should
            be measuring a Z stabilizer. Else, it measures a X stabilizer.
    """
    b1: Literal["x", "z"]
    b2: Literal["x", "z"]
    if top_left_is_z_stabilizer:
        b1, b2 = "z", "x"
    else:
        b1, b2 = "x", "z"
    return RPNGTemplate(
        template=QubitVerticalBorders(),
        mapping=FrozenDefaultDict(
            {
                # BOTTOM_RIGHT, normal plaquette
                2: RPNGDescription.from_string(f"---- ---- -x{b2}3- -{b2}4-"),
                # BOTTOM_LEFT, where the Hadamard transition occurs
                3: RPNGDescription.from_string(f"-{b1}1- x{b2}2- ---- ----"),
                # LEFT bulk, where the Hadamard transition occurs
                5: RPNGDescription.from_string(f"-{b1}1- x{b2}2- -{b1}3- x{b2}4-"),
                6: RPNGDescription.from_string(f"-{b2}1- x{b1}3- -{b2}2- x{b1}4-"),
                # RIGHT bulk, normal plaquettes
                7: RPNGDescription.from_string(f"x{b1}1- -{b1}3- x{b1}2- -{b1}4-"),
                8: RPNGDescription.from_string(f"x{b2}1- -{b2}2- x{b2}3- -{b2}4-"),
            },
            default_factory=lambda: RPNGDescription.from_string("---- ---- ---- ----"),
        ),
    )
