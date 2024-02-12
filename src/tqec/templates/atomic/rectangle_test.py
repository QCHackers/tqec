import numpy
import pytest
from tqec.exceptions import TQECException
from tqec.templates.atomic.rectangle import (
    AlternatingRectangleTemplate,
    RawRectangleTemplate,
)
from tqec.templates.scale import Dimension, FixedDimension, LinearFunction


@pytest.fixture
def dim2x2():
    return Dimension(2, LinearFunction(2))


@pytest.fixture
def dim3x2():
    return Dimension(3, LinearFunction(2))


@pytest.fixture
def dim2x40p3():
    return Dimension(2, LinearFunction(40, 3))


@pytest.fixture
def dim2():
    return FixedDimension(2)


def test_rectangle_template_init(dim2x2, dim3x2):
    AlternatingRectangleTemplate(dim2x2, dim3x2)


def test_rectangle_expected_plaquette_number(dim2x2, dim3x2):
    rect = AlternatingRectangleTemplate(dim2x2, dim3x2)
    assert rect.expected_plaquettes_number == 2


def test_rectangle_template_same_scaling(dim2x2, dim3x2):
    template = AlternatingRectangleTemplate(dim2x2, dim3x2)
    template.scale_to(30)
    shape = template.shape
    assert shape.x == 2 * 30
    assert shape.y == 2 * 30


def test_rectangle_template_different_scaling(dim2x2, dim2x40p3):
    template = AlternatingRectangleTemplate(dim2x2, dim2x40p3)
    template.scale_to(30)
    shape = template.shape
    assert shape.x == 2 * 30
    assert shape.y == 40 * 30 + 3


def test_rectangle_template_one_fixed_scaling(dim2x2, dim2):
    template = AlternatingRectangleTemplate(dim2x2, dim2)
    template.scale_to(30)
    shape = template.shape
    assert shape.x == 2 * 30
    assert shape.y == 2


def test_rectangle_template_one_fixed_scaling_instantiate_default_plaquettes(
    dim2x2, dim2
):
    template = AlternatingRectangleTemplate(dim2x2, dim2)
    arr = template.instantiate([1, 2])
    numpy.testing.assert_equal(arr, [[1, 2, 1, 2], [2, 1, 2, 1]])


def test_rectangle_template_one_fixed_scaling_instantiate_random_plaquettes(
    dim2x2, dim2
):
    template = AlternatingRectangleTemplate(dim2x2, dim2)
    arr = template.instantiate([78, 195])
    numpy.testing.assert_equal(arr, [[78, 195, 78, 195], [195, 78, 195, 78]])


def test_raw_rectangle_init():
    RawRectangleTemplate([[0]])


def test_raw_rectangle_larger_init():
    RawRectangleTemplate(
        [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    )


def test_raw_rectangle_shape():
    template = RawRectangleTemplate([[0]])
    assert template.shape.x == 1
    assert template.shape.y == 1


def test_raw_rectangle_larger_shape():
    template = RawRectangleTemplate(
        [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    )
    assert template.shape.x == 5
    assert template.shape.y == 5


def test_raw_rectangle_uneven_shape():
    template = RawRectangleTemplate([[0, 0, 0, 0, 0]])
    assert template.shape.x == 5
    assert template.shape.y == 1


def test_raw_rectangle_invalid_indices():
    with pytest.raises(TQECException):
        RawRectangleTemplate([[0], [0, 0]])


def test_raw_rectangle_scale_to_not_raising():
    RawRectangleTemplate([[0], [0]]).scale_to(94)


def test_raw_rectangle_simple_expected_plaquettes_number():
    template = RawRectangleTemplate([[0], [0]])
    assert template.expected_plaquettes_number == 1


def test_raw_rectangle_larger_expected_plaquettes_number():
    template = RawRectangleTemplate([[0], [1], [2]])
    assert template.expected_plaquettes_number == 3


def test_raw_rectangle_simple_instantiate():
    template = RawRectangleTemplate([[0]])
    arr = template.instantiate([1])
    numpy.testing.assert_equal(arr, [[1]])


def test_raw_rectangle_simple_instantiate_random_plaquette_index():
    template = RawRectangleTemplate([[0]])
    arr = template.instantiate([345897])
    numpy.testing.assert_equal(arr, [[345897]])


def test_raw_rectangle_larger_instantiate():
    template = RawRectangleTemplate([[0], [1], [2]])
    arr = template.instantiate([3, 2, 1])
    numpy.testing.assert_equal(arr, [[3], [2], [1]])


def test_raw_rectangle_larger_instantiate_different_order():
    template = RawRectangleTemplate([[0], [2], [1]])
    arr = template.instantiate([3, 2, 1])
    numpy.testing.assert_equal(arr, [[3], [1], [2]])


def test_raw_rectangle_with_noncontiguous_indices():
    with pytest.raises(TQECException, match="CONTIGUOUS indices"):
        RawRectangleTemplate([[0], [1], [24]])


def test_raw_rectangle_with_negative_index():
    with pytest.raises(TQECException, match="starting at 0"):
        RawRectangleTemplate([[-1]])
