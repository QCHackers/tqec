import numpy
import pytest
from tqec.position import Shape2D
from tqec.templates.atomic.square import AlternatingSquareTemplate
from tqec.templates.base import Template
from tqec.templates.scale import Dimension, FixedDimension, LinearFunction
from tqec.templates.shifted import ScalableOffset, ShiftedTemplate


@pytest.fixture
def default_template():
    return AlternatingSquareTemplate(Dimension(2, LinearFunction(2)))


@pytest.fixture
def zero_offset():
    return ScalableOffset(FixedDimension(0), FixedDimension(0))


@pytest.fixture
def scalable_offset():
    return ScalableOffset(
        Dimension(2, LinearFunction(2)), Dimension(2, LinearFunction(2))
    )


def test_scalable_offset_creation():
    ScalableOffset(FixedDimension(2), Dimension(2, LinearFunction(2)))


def test_scalable_offset_scaling():
    offset = ScalableOffset(
        Dimension(2, LinearFunction(3)), Dimension(2, LinearFunction(2))
    )
    assert offset.x.value == 6
    assert offset.y.value == 4
    offset.scale_to(4)
    assert offset.x.value == 12
    assert offset.y.value == 8


def test_zero_shifted_template(default_template: Template, zero_offset: ScalableOffset):
    template = ShiftedTemplate(default_template, zero_offset)
    assert (
        template.expected_plaquettes_number
        == default_template.expected_plaquettes_number
    )
    indices = list(range(1, template.expected_plaquettes_number + 1))
    numpy.testing.assert_equal(
        template.instantiate(*indices), default_template.instantiate(*indices)
    )


def test_shifted_template(default_template: Template, scalable_offset: ScalableOffset):
    template = ShiftedTemplate(default_template, scalable_offset)
    template.scale_to(1)
    assert (
        template.expected_plaquettes_number
        == default_template.expected_plaquettes_number
    )
    indices = list(range(1, template.expected_plaquettes_number + 1))
    assert template.shape == Shape2D(4, 4)
    numpy.testing.assert_equal(
        template.instantiate(*indices),
        [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 1, 2], [0, 0, 2, 1]],
    )
