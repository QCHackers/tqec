import numpy.testing
import pytest
from tqec.position import Shape2D
from tqec.templates.atomic.square import AlternatingSquareTemplate
from tqec.templates.base import Template
from tqec.templates.scale import Dimension, FixedDimension, LinearFunction
from tqec.templates.shifted import ScalableOffset, ShiftedTemplate
from tqec.templates.stack import StackedTemplate


@pytest.fixture
def small_alternating_template():
    return AlternatingSquareTemplate(Dimension(1, LinearFunction(2)))


@pytest.fixture
def shifted_small_alternating_template():
    return ShiftedTemplate(
        AlternatingSquareTemplate(Dimension(1, LinearFunction(2))),
        ScalableOffset(FixedDimension(2), FixedDimension(2)),
    )


@pytest.fixture
def larger_alternating_template():
    return AlternatingSquareTemplate(Dimension(1, LinearFunction(4)))


def test_stack_template_over_itself(small_alternating_template: Template):
    stack = StackedTemplate()
    stack.push_template_on_top(small_alternating_template)
    stack.push_template_on_top(small_alternating_template)
    instantiation = stack.instantiate(1, 2, 3, 4)

    numpy.testing.assert_equal(
        instantiation, small_alternating_template.instantiate(3, 4)
    )


def test_stack_small_alternating_on_top_of_larger_alternating(
    small_alternating_template: Template, larger_alternating_template: Template
):
    stack = StackedTemplate()
    stack.push_template_on_top(larger_alternating_template)
    stack.push_template_on_top(small_alternating_template)
    instantiation = stack.instantiate(1, 2, 3, 4)

    numpy.testing.assert_equal(
        instantiation, [[3, 4, 1, 2], [4, 3, 2, 1], [1, 2, 1, 2], [2, 1, 2, 1]]
    )


def test_stack_small_alternating_on_top_of_larger_alternating_expected_plaquette_number(
    small_alternating_template: Template, larger_alternating_template: Template
):
    stack = StackedTemplate()
    assert stack.expected_plaquettes_number == 0
    stack.push_template_on_top(larger_alternating_template)
    assert (
        stack.expected_plaquettes_number
        == larger_alternating_template.expected_plaquettes_number
    )
    stack.push_template_on_top(small_alternating_template)
    assert (
        stack.expected_plaquettes_number
        == larger_alternating_template.expected_plaquettes_number
        + small_alternating_template.expected_plaquettes_number
    )
    stack.pop_template_from_top()
    assert (
        stack.expected_plaquettes_number
        == larger_alternating_template.expected_plaquettes_number
    )


def test_stack_small_alternating_with_offset_on_top_of_larger_alternating(
    shifted_small_alternating_template: Template, larger_alternating_template: Template
):
    stack = StackedTemplate()
    stack.push_template_on_top(larger_alternating_template)
    stack.push_template_on_top(shifted_small_alternating_template)
    instantiation = stack.instantiate(1, 2, 3, 4)

    numpy.testing.assert_equal(
        instantiation,
        [[1, 2, 1, 2], [2, 1, 2, 1], [1, 2, 3, 4], [2, 1, 4, 3]],
    )


def test_stack_small_alternating_below_of_larger_alternating(
    small_alternating_template: Template, larger_alternating_template: Template
):
    stack = StackedTemplate()
    stack.push_template_on_top(small_alternating_template)
    stack.push_template_on_top(larger_alternating_template)
    instantiation = stack.instantiate(1, 2, 3, 4)

    numpy.testing.assert_equal(
        instantiation,
        larger_alternating_template.instantiate(3, 4),
    )


def test_stack_template_pop(
    small_alternating_template: Template, larger_alternating_template: Template
):
    stack = StackedTemplate()
    stack.push_template_on_top(larger_alternating_template)
    stack.push_template_on_top(small_alternating_template)
    stack.pop_template_from_top()
    instantiation = stack.instantiate(1, 2)

    numpy.testing.assert_equal(
        instantiation, larger_alternating_template.instantiate(1, 2)
    )


def test_stack_shape(
    small_alternating_template: Template, larger_alternating_template: Template
):
    stack = StackedTemplate()
    stack.push_template_on_top(small_alternating_template)
    assert stack.shape == Shape2D(2, 2)
    stack.push_template_on_top(larger_alternating_template)
    assert stack.shape == Shape2D(4, 4)
    stack.scale_to(2)
    assert stack.shape == Shape2D(8, 8)
    stack.pop_template_from_top()
    assert stack.shape == Shape2D(4, 4)


def test_stack_scale_to(
    small_alternating_template: Template, larger_alternating_template: Template
):
    stack = StackedTemplate()
    stack.push_template_on_top(larger_alternating_template)
    stack.push_template_on_top(small_alternating_template)
    stack.scale_to(2)
    instantiation = stack.instantiate(1, 2, 3, 4)
    numpy.testing.assert_equal(
        instantiation,
        [
            [3, 4, 3, 4, 1, 2, 1, 2],
            [4, 3, 4, 3, 2, 1, 2, 1],
            [3, 4, 3, 4, 1, 2, 1, 2],
            [4, 3, 4, 3, 2, 1, 2, 1],
            [1, 2, 1, 2, 1, 2, 1, 2],
            [2, 1, 2, 1, 2, 1, 2, 1],
            [1, 2, 1, 2, 1, 2, 1, 2],
            [2, 1, 2, 1, 2, 1, 2, 1],
        ],
    )
