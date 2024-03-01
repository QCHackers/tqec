import pytest

from tqec.templates.atomic import AlternatingSquareTemplate
from tqec.templates.atomic.rectangle import (
    AlternatingRectangleTemplate,
    RawRectangleTemplate,
)
from tqec.templates.base import TemplateWithIndices
from tqec.templates.composed import ComposedTemplate
from tqec.templates.scale import Dimension, FixedDimension, LinearFunction

_DIMENSIONS = [
    Dimension(2, LinearFunction(2, 0)),
    Dimension(2, LinearFunction(4, 0)),
    FixedDimension(1),
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
