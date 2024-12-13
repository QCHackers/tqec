from tqec.plaquette.enums import PlaquetteSide, ResetBasis
from tqec.plaquette.frozendefaultdict import FrozenDefaultDict
from tqec.plaquette.rpng import RPNGDescription
from tqec.templates.enums import ZObservableOrientation
from tqec.templates.indices.qubit import QubitTemplate
from tqec.templates.rpng import RPNGTemplate


def get_partial_reset_template(
    reset: ResetBasis,
    side: PlaquetteSide,
    orientation: ZObservableOrientation = ZObservableOrientation.HORIZONTAL,
) -> RPNGTemplate:
    r = reset.value.lower()
    # t/b: top/bottom
    # r/l: right/left
    tr, tl, br, bl = "----"
    match side:
        case PlaquetteSide.UP:
            tr, tl = r, r
        case PlaquetteSide.DOWN:
            br, bl = r, r
        case PlaquetteSide.RIGHT:
            tr, br = r, r
        case PlaquetteSide.LEFT:
            tl, bl = r, r

    bh = orientation.horizontal_basis()
    bv = orientation.vertical_basis()

    return RPNGTemplate(
        template=QubitTemplate(),
        mapping=FrozenDefaultDict(
            {
                # UP
                6: RPNGDescription.from_string(f"---- ---- {bl}{bv}3- {br}{bv}4-"),
                # LEFT
                7: RPNGDescription.from_string(f"---- {tl}{bh}3- ---- {bl}{bh}4-"),
                # Bulk
                9: RPNGDescription.from_string(
                    f"{tr}{bv}1- {tl}{bv}2- {br}{bv}3- {bl}{bv}4-"
                ),
                10: RPNGDescription.from_string(
                    f"{tr}{bh}1- {tl}{bh}3- {br}{bh}2- {bl}{bh}4-"
                ),
                # RIGHT
                12: RPNGDescription.from_string(f"{tr}{bh}1- ---- {br}{bh}2- ----"),
                # DOWN
                13: RPNGDescription.from_string(f"{tr}{bv}1- {tl}{bv}2- ---- ----"),
            },
            default_factory=lambda: RPNGDescription.from_string("---- ---- ---- ----"),
        ),
    )
