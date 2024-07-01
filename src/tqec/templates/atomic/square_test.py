import numpy
import pytest

from tqec.enums import CornerPositionEnum, TemplateOrientation
from tqec.exceptions import TQECException
from tqec.templates.atomic.square import (
    AlternatingCornerSquareTemplate,
    AlternatingSquareTemplate,
)
from tqec.templates.scale import LinearFunction


def test_square_template_init():
    dimension = LinearFunction(2)
    AlternatingSquareTemplate(dimension, k=2)


def test_square_expected_plaquette_number():
    dimension = LinearFunction(2)
    template = AlternatingSquareTemplate(dimension, k=2)
    assert template.expected_plaquettes_number == 2


def test_square_template_scaling():
    dimension = LinearFunction(2)
    template = AlternatingSquareTemplate(dimension)
    template.scale_to(30)
    shape = template.shape
    assert shape.x == 2 * 30
    assert shape.y == 2 * 30


def test_square_template_one_fixed_scaling():
    dimension = LinearFunction(0, 2)
    template = AlternatingSquareTemplate(dimension)
    template.scale_to(30)
    shape = template.shape
    assert shape.x == 2
    assert shape.y == 2


def test_square_template_instantiate_default_plaquettes():
    dimension = LinearFunction(2)
    template = AlternatingSquareTemplate(dimension)
    arr = template.instantiate([1, 2])
    numpy.testing.assert_equal(
        arr, [[1, 2, 1, 2], [2, 1, 2, 1], [1, 2, 1, 2], [2, 1, 2, 1]]
    )


def test_square_template_one_fixed_scaling_instantiate_random_plaquettes():
    dimension = LinearFunction(2)
    template = AlternatingSquareTemplate(dimension)
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


def test_corner_square_template_init():
    dimension = LinearFunction(2)
    AlternatingCornerSquareTemplate(dimension, CornerPositionEnum.LOWER_LEFT, k=2)


def test_corner_square_expected_plaquette_number():
    dimension = LinearFunction(2)
    rect = AlternatingCornerSquareTemplate(dimension, CornerPositionEnum.LOWER_LEFT)
    assert rect.expected_plaquettes_number == 5


def test_corner_square_template_scaling():
    dimension = LinearFunction(2)
    template = AlternatingCornerSquareTemplate(dimension, CornerPositionEnum.LOWER_LEFT)
    template.scale_to(30)
    shape = template.shape
    assert shape.x == 2 * 30
    assert shape.y == 2 * 30


def test_corner_square_template_one_fixed_scaling():
    dimension = LinearFunction(0, 2)
    template = AlternatingCornerSquareTemplate(dimension, CornerPositionEnum.LOWER_LEFT)
    template.scale_to(30)
    shape = template.shape
    assert shape.x == 2
    assert shape.y == 2


def test_corner_square_template_midline():
    dimension = LinearFunction(2)
    template = AlternatingCornerSquareTemplate(dimension, CornerPositionEnum.LOWER_LEFT)
    midline = template.get_midline_plaquettes()
    assert midline == [(1, 0), (1, 1), (1, 2), (1, 3)]
    midline = template.get_midline_plaquettes(TemplateOrientation.VERTICAL)
    assert midline == [(0, 1), (1, 1), (2, 1), (3, 1)]
    template.scale_to(4)
    midline = template.get_midline_plaquettes()
    assert midline == [
        (3, 0),
        (3, 1),
        (3, 2),
        (3, 3),
        (3, 4),
        (3, 5),
        (3, 6),
        (3, 7),
    ]
    template = AlternatingCornerSquareTemplate(
        LinearFunction(0, 3), CornerPositionEnum.LOWER_LEFT
    )
    with pytest.raises(TQECException, match="Midline is not defined for odd height."):
        template.get_midline_plaquettes()
