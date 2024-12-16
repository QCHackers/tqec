from typing import Final

from tqec.compile.specs.enums import JunctionArms
from tqec.plaquette.rpng import RPNGDescription
from tqec.templates.library.spatial import get_spatial_junction_qubit_template

_EMPT: Final[RPNGDescription] = RPNGDescription.from_string("---- ---- ---- ----")


def test_4_way_spatial_junction() -> None:
    description = get_spatial_junction_qubit_template(
        "z",
        JunctionArms.UP | JunctionArms.RIGHT | JunctionArms.DOWN | JunctionArms.LEFT,
    )
    instantiation = description.instantiate(k=2)

    _3STL = RPNGDescription.from_string("---- -z2- -z4- -z5-")
    _3SBR = RPNGDescription.from_string("-z1- -z2- -z4- ----")
    _ZVHE = RPNGDescription.from_string("-z1- -z4- -z3- -z5-")
    _ZHHE = RPNGDescription.from_string("-z1- -z2- -z3- -z4-")
    _XXXX = RPNGDescription.from_string("-x1- -x3- -x2- -x5-")
    assert instantiation == [
        [_3STL, _EMPT, _EMPT, _EMPT, _EMPT, _EMPT],
        [_EMPT, _ZVHE, _XXXX, _ZVHE, _XXXX, _EMPT],
        [_EMPT, _XXXX, _ZVHE, _XXXX, _ZHHE, _EMPT],
        [_EMPT, _ZHHE, _XXXX, _ZVHE, _XXXX, _EMPT],
        [_EMPT, _XXXX, _ZVHE, _XXXX, _ZVHE, _EMPT],
        [_EMPT, _EMPT, _EMPT, _EMPT, _EMPT, _3SBR],
    ]


def test_3_way_UP_RIGHT_DOWN_spatial_junction() -> None:
    description = get_spatial_junction_qubit_template(
        "z", JunctionArms.UP | JunctionArms.RIGHT | JunctionArms.DOWN
    )
    instantiation = description.instantiate(k=2)

    __Z_Z = RPNGDescription.from_string("---- -z3- ---- -z4-")
    _3SBR = RPNGDescription.from_string("-z1- -z2- -z4- ----")
    _ZVHE = RPNGDescription.from_string("-z1- -z4- -z3- -z5-")
    _ZHHE = RPNGDescription.from_string("-z1- -z2- -z3- -z4-")
    _XXXX = RPNGDescription.from_string("-x1- -x3- -x2- -x5-")

    assert instantiation == [
        [__Z_Z, _EMPT, _EMPT, _EMPT, _EMPT, _EMPT],
        [_EMPT, _ZVHE, _XXXX, _ZVHE, _XXXX, _EMPT],
        [__Z_Z, _XXXX, _ZVHE, _XXXX, _ZHHE, _EMPT],
        [_EMPT, _ZVHE, _XXXX, _ZVHE, _XXXX, _EMPT],
        [__Z_Z, _XXXX, _ZVHE, _XXXX, _ZVHE, _EMPT],
        [_EMPT, _EMPT, _EMPT, _EMPT, _EMPT, _3SBR],
    ]


def test_3_way_LEFT_UP_RIGHT_spatial_junction() -> None:
    description = get_spatial_junction_qubit_template(
        "z", JunctionArms.LEFT | JunctionArms.UP | JunctionArms.RIGHT
    )
    instantiation = description.instantiate(k=2)

    _3STL = RPNGDescription.from_string("---- -z2- -z4- -z5-")
    _ZZ__ = RPNGDescription.from_string("-z1- -z2- ---- ----")
    _ZVHE = RPNGDescription.from_string("-z1- -z4- -z3- -z5-")
    _ZHHE = RPNGDescription.from_string("-z1- -z2- -z3- -z4-")
    _XXXX = RPNGDescription.from_string("-x1- -x3- -x2- -x5-")

    assert instantiation == [
        [_3STL, _EMPT, _EMPT, _EMPT, _EMPT, _EMPT],
        [_EMPT, _ZVHE, _XXXX, _ZVHE, _XXXX, _EMPT],
        [_EMPT, _XXXX, _ZVHE, _XXXX, _ZHHE, _EMPT],
        [_EMPT, _ZHHE, _XXXX, _ZHHE, _XXXX, _EMPT],
        [_EMPT, _XXXX, _ZHHE, _XXXX, _ZHHE, _EMPT],
        [_EMPT, _ZZ__, _EMPT, _ZZ__, _EMPT, _ZZ__],
    ]


def test_2_way_through_spatial_junction() -> None:
    description = get_spatial_junction_qubit_template(
        "z", JunctionArms.LEFT | JunctionArms.RIGHT
    )
    instantiation = description.instantiate(k=2)

    _ZZ__ = RPNGDescription.from_string("-z1- -z2- ---- ----")
    ___ZZ = RPNGDescription.from_string("---- ---- -z3- -z4-")
    _ZHHE = RPNGDescription.from_string("-z1- -z2- -z3- -z4-")
    _XXXX = RPNGDescription.from_string("-x1- -x3- -x2- -x5-")

    assert instantiation == [
        [___ZZ, _EMPT, ___ZZ, _EMPT, ___ZZ, _EMPT],
        [_EMPT, _ZHHE, _XXXX, _ZHHE, _XXXX, _EMPT],
        [_EMPT, _XXXX, _ZHHE, _XXXX, _ZHHE, _EMPT],
        [_EMPT, _ZHHE, _XXXX, _ZHHE, _XXXX, _EMPT],
        [_EMPT, _XXXX, _ZHHE, _XXXX, _ZHHE, _EMPT],
        [_EMPT, _ZZ__, _EMPT, _ZZ__, _EMPT, _ZZ__],
    ]


def test_2_way_L_shape_spatial_junction() -> None:
    description = get_spatial_junction_qubit_template(
        "z", JunctionArms.DOWN | JunctionArms.RIGHT
    )
    instantiation = description.instantiate(k=2)

    L__ZZ = RPNGDescription.from_string("---- -z3- ---- -z4-")
    T__ZZ = RPNGDescription.from_string("---- ---- -z3- -z4-")
    _3STL = RPNGDescription.from_string("---- -z2- -z4- -z5-")
    _3SBR = RPNGDescription.from_string("-z1- -z2- -z4- ----")
    _ZVHE = RPNGDescription.from_string("-z1- -z4- -z3- -z5-")
    _ZHHE = RPNGDescription.from_string("-z1- -z2- -z3- -z4-")
    _XXXX = RPNGDescription.from_string("-x1- -x3- -x2- -x5-")

    assert instantiation == [
        [_EMPT, _EMPT, T__ZZ, _EMPT, T__ZZ, _EMPT],
        [_EMPT, _3STL, _XXXX, _ZHHE, _XXXX, _EMPT],
        [L__ZZ, _XXXX, _ZHHE, _XXXX, _ZHHE, _EMPT],
        [_EMPT, _ZVHE, _XXXX, _ZVHE, _XXXX, _EMPT],
        [L__ZZ, _XXXX, _ZVHE, _XXXX, _ZVHE, _EMPT],
        [_EMPT, _EMPT, _EMPT, _EMPT, _EMPT, _3SBR],
    ]
