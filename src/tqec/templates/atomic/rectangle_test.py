import pytest
from tqec.templates.atomic.rectangle import AlternatingRectangleTemplate
from tqec.templates.scale import Dimension


@pytest.fixture
def scaling_by_two_dimensions():
    return Dimension(2, lambda k: 2 * k), Dimension(3, lambda k: 2 * k)


def test_rectangle_template_init(
    scaling_by_two_dimensions: tuple[Dimension, Dimension],
):
    width, height = scaling_by_two_dimensions
    AlternatingRectangleTemplate(width, height)


def test_rectangle_template_same_scaling(
    scaling_by_two_dimensions: tuple[Dimension, Dimension],
):
    width, height = scaling_by_two_dimensions
    template = AlternatingRectangleTemplate(width, height)
    template.scale_to(30)
    shape = template.shape
    assert shape.x == 2 * 30
    assert shape.y == 2 * 30


def test_rectangle_template_different_scaling():
    width = Dimension(2, lambda x: 3 * x)
    height = Dimension(2, lambda x: 40 * x + 3)
    template = AlternatingRectangleTemplate(width, height)
    template.scale_to(30)
    shape = template.shape
    assert shape.x == 3 * 30
    assert shape.y == 40 * 30 + 3
