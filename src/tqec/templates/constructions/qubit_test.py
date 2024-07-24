from pprint import pprint

import pytest

from tqec.exceptions import TQECException
from tqec.templates.constructions.qubit import DenseQubitSquareTemplate
from tqec.templates.enums import TemplateOrientation
from tqec.templates.scale import LinearFunction


def test_qubit_square_midline():
    scalable_dimension = LinearFunction(2)
    constant_dimension = LinearFunction(0, 3)
    template = DenseQubitSquareTemplate(scalable_dimension, k=2)
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
    template = DenseQubitSquareTemplate(constant_dimension)
    with pytest.raises(TQECException, match="Midline is not defined for odd height."):
        template.get_midline_plaquettes()
