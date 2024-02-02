import numpy.testing
import pytest
from tqec.exceptions import TQECException
from tqec.position import Position, Shape2D
from tqec.templates.scalable.square import ScalableAlternatingSquare
from tqec.templates.stack import TemplateStack


def test_stack_template_over_itself():
    alternating = ScalableAlternatingSquare(2)
    stack = TemplateStack()
    stack.push_template_on_top(alternating)
    stack.push_template_on_top(alternating)
    instanciation = stack.instanciate(1, 2, 3, 4)

    numpy.testing.assert_array_equal(instanciation, alternating.instanciate(3, 4))


def test_stack_small_alternating_on_top_of_larger_alternating():
    small_alternating = ScalableAlternatingSquare(2)
    larger_alternating = ScalableAlternatingSquare(4)
    stack = TemplateStack()
    stack.push_template_on_top(larger_alternating)
    stack.push_template_on_top(small_alternating)
    instanciation = stack.instanciate(1, 2, 3, 4)

    numpy.testing.assert_array_equal(
        instanciation,
        numpy.array([[3, 4, 1, 2], [4, 3, 2, 1], [1, 2, 1, 2], [2, 1, 2, 1]]),
    )


def test_stack_small_alternating_with_offset_on_top_of_larger_alternating():
    small_alternating = ScalableAlternatingSquare(2)
    larger_alternating = ScalableAlternatingSquare(4)
    stack = TemplateStack()
    stack.push_template_on_top(larger_alternating)
    stack.push_template_on_top(small_alternating, positive_offset=Position(2, 2))
    instanciation = stack.instanciate(1, 2, 3, 4)

    numpy.testing.assert_array_equal(
        instanciation,
        numpy.array([[1, 2, 1, 2], [2, 1, 2, 1], [1, 2, 3, 4], [2, 1, 4, 3]]),
    )


def test_stack_small_alternating_below_of_larger_alternating():
    small_alternating = ScalableAlternatingSquare(2)
    larger_alternating = ScalableAlternatingSquare(4)
    stack = TemplateStack()
    stack.push_template_on_top(small_alternating)
    stack.push_template_on_top(larger_alternating)
    instanciation = stack.instanciate(1, 2, 3, 4)

    numpy.testing.assert_array_equal(
        instanciation,
        larger_alternating.instanciate(3, 4),
    )


def test_stack_template_pop():
    small_alternating = ScalableAlternatingSquare(2)
    larger_alternating = ScalableAlternatingSquare(4)
    stack = TemplateStack()
    stack.push_template_on_top(larger_alternating)
    stack.push_template_on_top(small_alternating)
    stack.pop_template_from_top()
    instanciation = stack.instanciate(1, 2)

    numpy.testing.assert_array_equal(
        instanciation, larger_alternating.instanciate(1, 2)
    )


def test_stack_shape():
    small_alternating = ScalableAlternatingSquare(2)
    stack = TemplateStack()
    stack.push_template_on_top(small_alternating)

    assert stack.shape == Shape2D(2, 2)


def test_stack_shape_with_offset():
    small_alternating = ScalableAlternatingSquare(2)
    stack = TemplateStack()
    stack.push_template_on_top(small_alternating, positive_offset=Position(18, 3))

    assert stack.shape == Shape2D(20, 5)


def test_stack_shape_with_negative_offset():
    small_alternating = ScalableAlternatingSquare(2)
    stack = TemplateStack()
    # We want the exception to include the offending non-positive offset in order for
    # the user to have an easy way to track down its mistake. This is done by the
    # match parameter below.
    with pytest.raises(TQECException, match=r".*\((x=)?-4, ?(y=)?-1\).*"):
        stack.push_template_on_top(small_alternating, positive_offset=Position(-4, -1))
