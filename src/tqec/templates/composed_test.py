import pytest

from tqec.exceptions import TQECException
from tqec.templates.atomic import AlternatingSquareTemplate
from tqec.templates.atomic.rectangle import (
    AlternatingRectangleTemplate,
    RawRectangleTemplate,
)
from tqec.templates.base import TemplateWithIndices
from tqec.templates.composed import ComposedTemplate
from tqec.templates.constructions.grid import TemplateGrid
from tqec.templates.constructions.qubit import DenseQubitSquareTemplate
from tqec.templates.enums import CornerPositionEnum
from tqec.templates.scale import LinearFunction

_DIMENSIONS = [
    LinearFunction(2, 0),
    LinearFunction(4, 0),
    LinearFunction(0, 1),
]
_TEMPLATES_AND_INDICES = [
    (AlternatingSquareTemplate(_DIMENSIONS[0]), [1, 2]),
    (AlternatingRectangleTemplate(_DIMENSIONS[0], _DIMENSIONS[1]), [198345, 21]),
    (AlternatingRectangleTemplate(_DIMENSIONS[0], _DIMENSIONS[2]), [0, 68]),
    (RawRectangleTemplate([[0]]), [1]),
]


def test_empty():
    template = ComposedTemplate([])
    assert template.expected_plaquettes_number == 0
    assert template.shape.to_numpy_shape() == (0, 0)


@pytest.mark.parametrize("atomic_template_and_indices", _TEMPLATES_AND_INDICES)
def test_one_template(atomic_template_and_indices):
    atomic_template, indices = atomic_template_and_indices
    template = ComposedTemplate([TemplateWithIndices(atomic_template, indices)])
    assert template.shape == atomic_template.shape
    assert template.expected_plaquettes_number == max(indices)


def get_collapsing_template() -> ComposedTemplate:
    #  2  3  4  5  6
    #  1           7
    #  0..0.. ..8..8
    square_1x1 = TemplateWithIndices(RawRectangleTemplate([[0]]), [1])
    rect_2kx1 = TemplateWithIndices(
        AlternatingRectangleTemplate(LinearFunction(2), LinearFunction(0, 1)), [2, 3]
    )
    templates = [
        rect_2kx1,
        square_1x1,
        square_1x1,
        square_1x1,
        square_1x1,
        square_1x1,
        square_1x1,
        square_1x1,
        rect_2kx1,
    ]
    template = ComposedTemplate(templates)
    for i in [1, 2]:
        template.add_corner_relation(
            (i - 1, CornerPositionEnum.UPPER_LEFT), (i, CornerPositionEnum.LOWER_LEFT)
        )
    for i in [3, 4, 5, 6]:
        template.add_corner_relation(
            (i - 1, CornerPositionEnum.LOWER_RIGHT), (i, CornerPositionEnum.LOWER_LEFT)
        )
    for i in [7, 8]:
        template.add_corner_relation(
            (i - 1, CornerPositionEnum.LOWER_RIGHT), (i, CornerPositionEnum.UPPER_RIGHT)
        )
    return template


def test_validation_collapsing_composed_template():
    template = get_collapsing_template()

    assert not template.is_valid()
    expected_error_message = r"""^Invalid ComposedTemplate instance\. The following templates overlap on the shown intervals:
  On \(1.25, inf\), templates 0 and 8 overlap$"""
    with pytest.raises(TQECException, match=expected_error_message):
        template.assert_is_valid()

    template = TemplateGrid(3, 2, DenseQubitSquareTemplate(LinearFunction(2)))
    template.assert_is_valid()
