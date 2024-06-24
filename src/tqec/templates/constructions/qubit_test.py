import pytest

from tqec.enums import TemplateOrientation
from tqec.exceptions import TQECException
from tqec.templates.constructions.qubit import (
    QubitRectangleTemplate,
    QubitSquareTemplate,
)
from tqec.templates.scale import LinearFunction


def test_qubit_square_midline():
    scalable_dimension = LinearFunction(2)
    constant_dimension = LinearFunction(0, 3)
    template = QubitSquareTemplate(scalable_dimension)
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
    template = QubitSquareTemplate(constant_dimension)
    with pytest.raises(TQECException, match="Midline is not defined for odd height."):
        template.get_midline_plaquettes()


def test_qubit_rectangle_midline():
    width = LinearFunction(2)
    height = LinearFunction(3)
    template = QubitRectangleTemplate(width, height, k=2)
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
        (4, 13),
    ]
    template.scale_to(3)
    with pytest.raises(TQECException, match="Midline is not defined for odd width."):
        template.get_midline_plaquettes(TemplateOrientation.VERTICAL)
