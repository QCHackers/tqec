from typing import Literal

from tqec.plaquette.enums import MeasurementBasis, ResetBasis
from tqec.plaquette.frozendefaultdict import FrozenDefaultDict
from tqec.plaquette.rpng import RPNGDescription
from tqec.templates.enums import ZObservableOrientation
from tqec.templates.indices.qubit import QubitTemplate
from tqec.templates.rpng import RPNGTemplate


def get_memory_template(
    orientation: ZObservableOrientation = ZObservableOrientation.HORIZONTAL,
    reset: ResetBasis | None = None,
    measurement: MeasurementBasis | None = None,
) -> RPNGTemplate:
    """Implementation of standard memory rounds.

    Note:
        this function does not enforce anything on the input values. As such, it
        is possible to generate a description of a round that will both reset and
        measure the data-qubits.

    Arguments:
        orientation: orientation of the Z observable. Used to compute the
            stabilizers that should be measured on the boundaries and in the
            bulk of the returned logical qubit description.
        reset: basis of the reset operation performed on data-qubits. Defaults
            to ``None`` that translates to no reset being applied on data-qubits.
        measurement: basis of the measurement operation performed on data-qubits.
            Defaults to ``None`` that translates to no measurement being applied
            on data-qubits.

    Returns:
        a description of a standard memory round, optionally with resets or
        measurements on the data-qubits too.
    """
    # r/m: reset/measurement basis applied to each data-qubit
    r = reset.value.lower() if reset is not None else "-"
    m = measurement.value.lower() if measurement is not None else "-"
    # bh: basis horizontal, bv: basis vertical
    bh = orientation.horizontal_basis()
    bv = orientation.vertical_basis()

    return RPNGTemplate(
        template=QubitTemplate(),
        mapping=FrozenDefaultDict(
            {
                # UP
                6: RPNGDescription.from_string(f"---- ---- {r}{bv}3{m} {r}{bv}4{m}"),
                # LEFT
                7: RPNGDescription.from_string(f"---- {r}{bh}3{m} ---- {r}{bh}4{m}"),
                # Bulk
                9: RPNGDescription.from_string(
                    f"{r}{bv}1{m} {r}{bv}2{m} {r}{bv}3{m} {r}{bv}4{m}"
                ),
                10: RPNGDescription.from_string(
                    f"{r}{bh}1{m} {r}{bh}3{m} {r}{bh}2{m} {r}{bh}4{m}"
                ),
                # RIGHT
                12: RPNGDescription.from_string(f"{r}{bh}1{m} ---- {r}{bh}2{m} ----"),
                # DOWN
                13: RPNGDescription.from_string(f"{r}{bv}1{m} {r}{bv}2{m} ---- ----"),
            },
            default_factory=lambda: RPNGDescription.from_string("---- ---- ---- ----"),
        ),
    )
