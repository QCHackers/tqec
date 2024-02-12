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
    return AlternatingSquareTemplate(Dimension(2, LinearFunction(2)))


def test_stack_template_over_itself(small_alternating_template: Template):
    stack = StackedTemplate()
    stack.push_template_on_top(small_alternating_template)
    stack.push_template_on_top(small_alternating_template)
    instanciation = stack.instantiate([1, 2, 3, 4])

    numpy.testing.assert_array_equal(
        instanciation, small_alternating_template.instantiate([3, 4])
    )


def test_stack_small_alternating_on_top_of_larger_alternating(
    small_alternating_template: Template, larger_alternating_template: Template
):
    stack = StackedTemplate()
    stack.push_template_on_top(larger_alternating_template)
    stack.push_template_on_top(small_alternating_template)
    instanciation = stack.instantiate([1, 2, 3, 4])

    numpy.testing.assert_array_equal(
        instanciation,
        numpy.array([[3, 4, 1, 2], [4, 3, 2, 1], [1, 2, 1, 2], [2, 1, 2, 1]]),
    )


def test_stack_small_alternating_with_offset_on_top_of_larger_alternating(
    shifted_small_alternating_template: Template, larger_alternating_template: Template
):
    stack = StackedTemplate()
    stack.push_template_on_top(larger_alternating_template)
    stack.push_template_on_top(shifted_small_alternating_template)
    instanciation = stack.instantiate([1, 2, 3, 4])

    numpy.testing.assert_array_equal(
        instanciation,
        numpy.array([[1, 2, 1, 2], [2, 1, 2, 1], [1, 2, 3, 4], [2, 1, 4, 3]]),
    )


def test_stack_small_alternating_below_of_larger_alternating(
    small_alternating_template: Template, larger_alternating_template: Template
):
    stack = StackedTemplate()
    stack.push_template_on_top(small_alternating_template)
    stack.push_template_on_top(larger_alternating_template)
    instanciation = stack.instantiate([1, 2, 3, 4])

    numpy.testing.assert_array_equal(
        instanciation,
        larger_alternating_template.instantiate([3, 4]),
    )


def test_stack_template_pop(
    small_alternating_template: Template, larger_alternating_template: Template
):
    stack = StackedTemplate()
    stack.push_template_on_top(larger_alternating_template)
    stack.push_template_on_top(small_alternating_template)
    stack.pop_template_from_top()
    instanciation = stack.instantiate([1, 2])

    numpy.testing.assert_array_equal(
        instanciation, larger_alternating_template.instantiate([1, 2])
    )


def test_stack_shape(small_alternating_template: Template):
    stack = StackedTemplate()
    stack.push_template_on_top(small_alternating_template)

    assert stack.shape == Shape2D(2, 2)
