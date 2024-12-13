from tqec.plaquette.enums import MeasurementBasis, PlaquetteSide
from tqec.plaquette.frozendefaultdict import FrozenDefaultDict
from tqec.plaquette.rpng import RPNGDescription
from tqec.templates.indices.qubit import QubitTemplate
from tqec.templates.rpng import RPNGTemplate


def get_partial_measurement_template(
    measurement: MeasurementBasis, side: PlaquetteSide
) -> RPNGTemplate:
    m = measurement.value.lower()
    # t/b: top/bottom
    # r/l: right/left
    tr, tl, br, bl = "----"
    match side:
        case PlaquetteSide.UP:
            tr, tl = m, m
        case PlaquetteSide.DOWN:
            br, bl = m, m
        case PlaquetteSide.RIGHT:
            tr, br = m, m
        case PlaquetteSide.LEFT:
            tl, bl = m, m

    return RPNGTemplate(
        template=QubitTemplate(),
        mapping=FrozenDefaultDict(
            {
                # XX_UP
                6: RPNGDescription.from_string(f"---- ---- {br}x3- {bl}x4-"),
                # ZZ_LEFT
                7: RPNGDescription.from_string(f"---- {tl}z3- ---- {bl}z4-"),
                # XXXX
                9: RPNGDescription.from_string(f"{tr}x1- {tl}x2- {br}x3- {bl}x4-"),
                # ZZZZ
                10: RPNGDescription.from_string(f"{tr}z1- {tl}z3- {br}z2- {bl}z4-"),
                # ZZ_RIGHT
                12: RPNGDescription.from_string(f"{tr}z1- ---- {br}z2- ----"),
                # XX_DOWN
                13: RPNGDescription.from_string(f"{tr}x1- {tl}x2- ---- ----"),
            },
            default_factory=lambda: RPNGDescription.from_string("---- ---- ---- ----"),
        ),
    )
