import numpy
import pytest

from tqec.enums import TemplateOrientation
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


@pytest.fixture
def dim2x3():
    return Dimension(2, LinearFunction(3))


def test_rectangle_template_init(dim2x2, dim3x2):
    AlternatingRectangleTemplate(dim2x2, dim3x2)


def test_rectangle_expected_plaquette_number(dim2x2, dim3x2):
    rect = AlternatingRectangleTemplate(dim2x2, dim3x2)
    assert rect.expected_plaquettes_number == 2


def test_rectangle_template_same_scaling(dim2x2, dim3x2):
    template = AlternatingRectangleTemplate(dim2x2, dim3x2)
    template.scale_to(30)
    shape = template.shape
    assert shape.x.value == 2 * 30
    assert shape.y.value == 2 * 30


def test_rectangle_template_different_scaling(dim2x2, dim2x40p3):
    template = AlternatingRectangleTemplate(dim2x2, dim2x40p3)
    template.scale_to(30)
    shape = template.shape
    assert shape.x.value == 2 * 30
    assert shape.y.value == 40 * 30 + 3


def test_rectangle_template_one_fixed_scaling(dim2x2, dim2):
    template = AlternatingRectangleTemplate(dim2x2, dim2)
    template.scale_to(30)
    shape = template.shape
    assert shape.x.value == 2 * 30
    assert shape.y.value == 2


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


def test_raw_rectangle_empty_init():
    with pytest.raises(TQECException):
        RawRectangleTemplate([[]])


def test_raw_rectangle_wrongly_sized_init():
    with pytest.raises(TQECException):
        RawRectangleTemplate([[0, 1], [1]])


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
    assert template.shape.x.value == 1
    assert template.shape.y.value == 1


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
    assert template.shape.x.value == 5
    assert template.shape.y.value == 5


def test_raw_rectangle_uneven_shape():
    template = RawRectangleTemplate([[0, 0, 0, 0, 0]])
    assert template.shape.x.value == 5
    assert template.shape.y.value == 1


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


def test_raw_rectangle_midline():
    template = RawRectangleTemplate(
        [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
    )
    midline = template.get_midline_plaquettes()
    assert midline == [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5)]
    midline = template.get_midline_plaquettes(TemplateOrientation.VERTICAL)
    assert midline == [(0, 2), (1, 2), (2, 2), (3, 2)]
    template.scale_to(4)
    midline = template.get_midline_plaquettes()
    # shoudl be 4*3 elements
    template = RawRectangleTemplate([[0]])
    with pytest.raises(TQECException, match="Midline is not defined for odd height."):
        template.get_midline_plaquettes()


def test_rectangle_midline(dim2x2, dim2x3):
    template = AlternatingRectangleTemplate(dim2x2, dim2x3)
    midline = template.get_midline_plaquettes()
    assert midline == [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5)]
    midline = template.get_midline_plaquettes(TemplateOrientation.VERTICAL)
    assert midline == [(0, 2), (1, 2), (2, 2), (3, 2)]
    template.scale_to(4)
    midline = template.get_midline_plaquettes()
    # shoudl be 4*3 elements
    assert midline == [
        (3, 0),
        (3, 1),
        (3, 2),
        (3, 3),
        (3, 4),
        (3, 5),
        (3, 6),
        (3, 7),
        (3, 8),
        (3, 9),
        (3, 10),
        (3, 11),
    ]
    template.scale_to(3)
    with pytest.raises(TQECException, match="Midline is not defined for odd width."):
        template.get_midline_plaquettes(TemplateOrientation.VERTICAL)
