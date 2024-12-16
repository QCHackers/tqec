from tqec.plaquette.enums import MeasurementBasis, ResetBasis
from tqec.plaquette.rpng import RPNGDescription
from tqec.templates.enums import ZObservableOrientation
from tqec.templates.indices.qubit import QubitTemplate
from tqec.templates.library.memory import get_memory_qubit_template


def test_memory_horizontal_z_observable() -> None:
    memory_template = get_memory_qubit_template(ZObservableOrientation.HORIZONTAL)
    assert isinstance(memory_template.template, QubitTemplate)
    plaquettes = memory_template.mapping
    assert plaquettes[1] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[2] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[3] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[4] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[5] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[6] == RPNGDescription.from_string("---- ---- -x3- -x4-")
    assert plaquettes[7] == RPNGDescription.from_string("---- -z3- ---- -z4-")
    assert plaquettes[8] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[9] == RPNGDescription.from_string("-x1- -x2- -x3- -x4-")
    assert plaquettes[10] == RPNGDescription.from_string("-z1- -z3- -z2- -z4-")
    assert plaquettes[11] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[12] == RPNGDescription.from_string("-z1- ---- -z2- ----")
    assert plaquettes[13] == RPNGDescription.from_string("-x1- -x2- ---- ----")
    assert plaquettes[14] == RPNGDescription.from_string("---- ---- ---- ----")


def test_memory_vertical_z_observable() -> None:
    memory_template = get_memory_qubit_template(ZObservableOrientation.VERTICAL)
    assert isinstance(memory_template.template, QubitTemplate)
    plaquettes = memory_template.mapping
    assert plaquettes[1] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[2] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[3] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[4] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[5] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[6] == RPNGDescription.from_string("---- ---- -z3- -z4-")
    assert plaquettes[7] == RPNGDescription.from_string("---- -x3- ---- -x4-")
    assert plaquettes[8] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[9] == RPNGDescription.from_string("-z1- -z2- -z3- -z4-")
    assert plaquettes[10] == RPNGDescription.from_string("-x1- -x3- -x2- -x4-")
    assert plaquettes[11] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[12] == RPNGDescription.from_string("-x1- ---- -x2- ----")
    assert plaquettes[13] == RPNGDescription.from_string("-z1- -z2- ---- ----")
    assert plaquettes[14] == RPNGDescription.from_string("---- ---- ---- ----")


def test_memory_vertical_z_observable_reset_z() -> None:
    memory_template = get_memory_qubit_template(
        ZObservableOrientation.VERTICAL, reset=ResetBasis.Z
    )
    assert isinstance(memory_template.template, QubitTemplate)
    plaquettes = memory_template.mapping
    assert plaquettes[1] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[2] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[3] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[4] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[5] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[6] == RPNGDescription.from_string("---- ---- zz3- zz4-")
    assert plaquettes[7] == RPNGDescription.from_string("---- zx3- ---- zx4-")
    assert plaquettes[8] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[9] == RPNGDescription.from_string("zz1- zz2- zz3- zz4-")
    assert plaquettes[10] == RPNGDescription.from_string("zx1- zx3- zx2- zx4-")
    assert plaquettes[11] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[12] == RPNGDescription.from_string("zx1- ---- zx2- ----")
    assert plaquettes[13] == RPNGDescription.from_string("zz1- zz2- ---- ----")
    assert plaquettes[14] == RPNGDescription.from_string("---- ---- ---- ----")


def test_memory_vertical_z_observable_measure_x() -> None:
    memory_template = get_memory_qubit_template(
        ZObservableOrientation.VERTICAL, measurement=MeasurementBasis.X
    )
    assert isinstance(memory_template.template, QubitTemplate)
    plaquettes = memory_template.mapping
    assert plaquettes[1] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[2] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[3] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[4] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[5] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[6] == RPNGDescription.from_string("---- ---- -z3x -z4x")
    assert plaquettes[7] == RPNGDescription.from_string("---- -x3x ---- -x4x")
    assert plaquettes[8] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[9] == RPNGDescription.from_string("-z1x -z2x -z3x -z4x")
    assert plaquettes[10] == RPNGDescription.from_string("-x1x -x3x -x2x -x4x")
    assert plaquettes[11] == RPNGDescription.from_string("---- ---- ---- ----")
    assert plaquettes[12] == RPNGDescription.from_string("-x1x ---- -x2x ----")
    assert plaquettes[13] == RPNGDescription.from_string("-z1x -z2x ---- ----")
    assert plaquettes[14] == RPNGDescription.from_string("---- ---- ---- ----")
