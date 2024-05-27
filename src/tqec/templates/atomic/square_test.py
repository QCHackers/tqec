import numpy
import pytest

from tqec.enums import CornerPositionEnum
from tqec.templates.atomic.square import (
    AlternatingCornerSquareTemplate,
    AlternatingSquareTemplate,
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


def test_square_template_init(dim2x2):
    AlternatingSquareTemplate(dim2x2)


def test_square_expected_plaquette_number(dim2x2):
    rect = AlternatingSquareTemplate(dim2x2)
    assert rect.expected_plaquettes_number == 2


def test_square_template_scaling(dim2x2):
    template = AlternatingSquareTemplate(dim2x2)
    template.scale_to(30)
    shape = template.shape
    assert shape.x.value == 2 * 30
    assert shape.y.value == 2 * 30


def test_square_template_one_fixed_scaling(dim2):
    template = AlternatingSquareTemplate(dim2)
    template.scale_to(30)
    shape = template.shape
    assert shape.x.value == 2
    assert shape.y.value == 2


def test_square_template_instantiate_default_plaquettes(dim2x2):
    template = AlternatingSquareTemplate(dim2x2)
    arr = template.instantiate([1, 2])
    numpy.testing.assert_equal(
        arr, [[1, 2, 1, 2], [2, 1, 2, 1], [1, 2, 1, 2], [2, 1, 2, 1]]
    )


def test_square_template_one_fixed_scaling_instantiate_random_plaquettes(dim2x2, dim2):
    template = AlternatingSquareTemplate(dim2x2, dim2)
    arr = template.instantiate([78, 195])
    numpy.testing.assert_equal(
        arr,
        [
            [78, 195, 78, 195],
            [195, 78, 195, 78],
            [78, 195, 78, 195],
            [195, 78, 195, 78],
        ],
    )


def test_corner_square_template_init(dim2x2):
    AlternatingCornerSquareTemplate(dim2x2, CornerPositionEnum.LOWER_LEFT)


def test_corner_square_expected_plaquette_number(dim2x2):
    rect = AlternatingCornerSquareTemplate(dim2x2, CornerPositionEnum.LOWER_LEFT)
    assert rect.expected_plaquettes_number == 5


def test_corner_square_template_scaling(dim2x2):
    template = AlternatingCornerSquareTemplate(dim2x2, CornerPositionEnum.LOWER_LEFT)
    template.scale_to(30)
    shape = template.shape
    assert shape.x.value == 2 * 30
    assert shape.y.value == 2 * 30


def test_corner_square_template_one_fixed_scaling(dim2):
    template = AlternatingCornerSquareTemplate(dim2, CornerPositionEnum.LOWER_LEFT)
    template.scale_to(30)
    shape = template.shape
    assert shape.x.value == 2
    assert shape.y.value == 2
