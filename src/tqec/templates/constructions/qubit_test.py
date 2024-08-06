import itertools

import numpy.testing
import pytest

from tqec.exceptions import TQECException
from tqec.templates.constructions.qubit import (
    DenseQubitSquareTemplate,
    QubitHorizontalBorders,
    QubitVerticalBorders,
)
from tqec.templates.enums import TemplateOrientation, TemplateSide
from tqec.templates.scale import LinearFunction


def test_qubit_square_midline() -> None:
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


def test_qubit_square() -> None:
    template = DenseQubitSquareTemplate(LinearFunction(2, 0), k=2)
    template_array = template.instantiate(
        list(range(1, template.expected_plaquettes_number + 1))
    )
    numpy.testing.assert_allclose(
        template_array,
        [
            [1, 5, 6, 5, 6, 2],
            [7, 9, 10, 9, 10, 11],
            [8, 10, 9, 10, 9, 12],
            [7, 9, 10, 9, 10, 11],
            [8, 10, 9, 10, 9, 12],
            [3, 13, 14, 13, 14, 4],
        ],
    )
    _expected_indices_on_sides = {
        TemplateSide.BOTTOM: {13, 14},
        TemplateSide.BOTTOM_LEFT: {3},
        TemplateSide.BOTTOM_RIGHT: {4},
        TemplateSide.LEFT: {7, 8},
        TemplateSide.RIGHT: {11, 12},
        TemplateSide.TOP: {5, 6},
        TemplateSide.TOP_LEFT: {1},
        TemplateSide.TOP_RIGHT: {2},
    }
    for side, expected_indices in _expected_indices_on_sides.items():
        assert set(template.get_plaquette_indices_on_sides([side])) == expected_indices
        duplicated_side_indices = template.get_plaquette_indices_on_sides([side, side])
        assert (
            len(duplicated_side_indices) == len(expected_indices)
            and set(duplicated_side_indices) == expected_indices
        )
    for sides in itertools.combinations(_expected_indices_on_sides.keys(), 2):
        assert set(template.get_plaquette_indices_on_sides(list(sides))) == (
            _expected_indices_on_sides[sides[0]] | _expected_indices_on_sides[sides[1]]
        )


def test_qubit_vertical_border() -> None:
    template = QubitVerticalBorders(LinearFunction(2, 0), k=2)
    template_array = template.instantiate(
        list(range(1, template.expected_plaquettes_number + 1))
    )
    numpy.testing.assert_allclose(
        template_array,
        [[1, 5], [2, 6], [3, 7], [2, 6], [3, 7], [4, 8]],
    )
    _expected_indices_on_sides = {
        TemplateSide.BOTTOM: set(),
        TemplateSide.BOTTOM_LEFT: {4},
        TemplateSide.BOTTOM_RIGHT: {8},
        TemplateSide.LEFT: {2, 3},
        TemplateSide.RIGHT: {6, 7},
        TemplateSide.TOP: set(),
        TemplateSide.TOP_LEFT: {1},
        TemplateSide.TOP_RIGHT: {5},
    }
    for side, expected_indices in _expected_indices_on_sides.items():
        assert set(template.get_plaquette_indices_on_sides([side])) == expected_indices
        duplicated_side_indices = template.get_plaquette_indices_on_sides([side, side])
        assert (
            len(duplicated_side_indices) == len(expected_indices)
            and set(duplicated_side_indices) == expected_indices
        )
    for sides in itertools.combinations(_expected_indices_on_sides.keys(), 2):
        assert set(template.get_plaquette_indices_on_sides(list(sides))) == (
            _expected_indices_on_sides[sides[0]] | _expected_indices_on_sides[sides[1]]
        )


def test_qubit_horizontal_border() -> None:
    template = QubitHorizontalBorders(LinearFunction(2, 0), k=2)
    template_array = template.instantiate(
        list(range(1, template.expected_plaquettes_number + 1))
    )
    numpy.testing.assert_allclose(
        template_array,
        [[1, 2, 3, 2, 3, 4], [5, 6, 7, 6, 7, 8]],
    )
    _expected_indices_on_sides = {
        TemplateSide.BOTTOM: {6, 7},
        TemplateSide.BOTTOM_LEFT: {5},
        TemplateSide.BOTTOM_RIGHT: {8},
        TemplateSide.LEFT: set(),
        TemplateSide.RIGHT: set(),
        TemplateSide.TOP: {2, 3},
        TemplateSide.TOP_LEFT: {1},
        TemplateSide.TOP_RIGHT: {4},
    }
    for side, expected_indices in _expected_indices_on_sides.items():
        assert set(template.get_plaquette_indices_on_sides([side])) == expected_indices
        duplicated_side_indices = template.get_plaquette_indices_on_sides([side, side])
        assert (
            len(duplicated_side_indices) == len(expected_indices)
            and set(duplicated_side_indices) == expected_indices
        )
    for sides in itertools.combinations(_expected_indices_on_sides.keys(), 2):
        assert set(template.get_plaquette_indices_on_sides(list(sides))) == (
            _expected_indices_on_sides[sides[0]] | _expected_indices_on_sides[sides[1]]
        )
