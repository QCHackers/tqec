import pytest
from tqec.enums import TemplateOrientation
from tqec.templates.constructions.qubit import (
    QubitRectangleTemplate,
    QubitSquareTemplate,
)
from tqec.templates.scale import Dimension, FixedDimension, LinearFunction


@pytest.fixture
def dim2x2():
    return Dimension(2, LinearFunction(2))


@pytest.fixture
def dim2x3():
    return Dimension(2, LinearFunction(3))


@pytest.fixture
def dim2():
    return FixedDimension(2)


def test_qubit_square_midline(dim2x2):
    template = QubitSquareTemplate(dim2x2)
    midline = template.get_midline_plaquettes()
    assert midline == [(2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5)]
    midline = template.get_midline_plaquettes(TemplateOrientation.VERTICAL)
    assert midline == [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2)]
    template.scale_to(4)
    midline = template.get_midline_plaquettes()
    assert midline == [
        (4, 0),
        (4, 1),
        (4, 2),
        (4, 3),
        (4, 4),
        (4, 5),
        (4, 6),
        (4, 7),
        (4, 8),
        (4, 9),
    ]


def test_qubit_rectangle_midline(dim2x2, dim2x3):
    template = QubitRectangleTemplate(dim2x2, dim2x3)
    midline = template.get_midline_plaquettes()
    assert midline == [(2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7)]
    midline = template.get_midline_plaquettes(TemplateOrientation.VERTICAL)
    assert midline == [(0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3)]
    template.scale_to(4)
    midline = template.get_midline_plaquettes()
    # shoudl be 4*3+2 elements
    assert midline == [
        (4, 0),
        (4, 1),
        (4, 2),
        (4, 3),
        (4, 4),
        (4, 5),
        (4, 6),
        (4, 7),
        (4, 8),
        (4, 9),
        (4, 10),
        (4, 11),
        (4, 12),
        (4, 13)
    ]
