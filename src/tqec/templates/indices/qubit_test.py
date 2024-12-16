import numpy
import pytest

from tqec.exceptions import TQECWarning
from tqec.scale import LinearFunction, Scalable2D
from tqec.templates.indices.qubit import (
    QubitHorizontalBorders,
    QubitSpatialJunctionTemplate,
    QubitTemplate,
    QubitVerticalBorders,
)


def test_creation() -> None:
    QubitTemplate()
    QubitHorizontalBorders()
    QubitVerticalBorders()
    QubitSpatialJunctionTemplate()


def test_expected_plaquettes_number() -> None:
    assert QubitTemplate().expected_plaquettes_number == 14
    assert QubitHorizontalBorders().expected_plaquettes_number == 8
    assert QubitVerticalBorders().expected_plaquettes_number == 8
    assert QubitSpatialJunctionTemplate().expected_plaquettes_number == 15


def test_scalable_shape() -> None:
    assert QubitTemplate().scalable_shape == Scalable2D(
        LinearFunction(2, 2), LinearFunction(2, 2)
    )
    assert QubitHorizontalBorders().scalable_shape == Scalable2D(
        LinearFunction(2, 2), LinearFunction(0, 2)
    )
    assert QubitVerticalBorders().scalable_shape == Scalable2D(
        LinearFunction(0, 2), LinearFunction(2, 2)
    )
    assert QubitSpatialJunctionTemplate().scalable_shape == Scalable2D(
        LinearFunction(2, 2), LinearFunction(2, 2)
    )


def test_qubit_template_instantiation() -> None:
    template = QubitTemplate()
    numpy.testing.assert_array_equal(
        template.instantiate(2),
        [
            [1, 5, 6, 5, 6, 2],
            [7, 9, 10, 9, 10, 11],
            [8, 10, 9, 10, 9, 12],
            [7, 9, 10, 9, 10, 11],
            [8, 10, 9, 10, 9, 12],
            [3, 13, 14, 13, 14, 4],
        ],
    )
    numpy.testing.assert_array_equal(
        template.instantiate(4),
        [
            [1, 5, 6, 5, 6, 5, 6, 5, 6, 2],
            [7, 9, 10, 9, 10, 9, 10, 9, 10, 11],
            [8, 10, 9, 10, 9, 10, 9, 10, 9, 12],
            [7, 9, 10, 9, 10, 9, 10, 9, 10, 11],
            [8, 10, 9, 10, 9, 10, 9, 10, 9, 12],
            [7, 9, 10, 9, 10, 9, 10, 9, 10, 11],
            [8, 10, 9, 10, 9, 10, 9, 10, 9, 12],
            [7, 9, 10, 9, 10, 9, 10, 9, 10, 11],
            [8, 10, 9, 10, 9, 10, 9, 10, 9, 12],
            [3, 13, 14, 13, 14, 13, 14, 13, 14, 4],
        ],
    )


def test_qubit_horizontal_borders_template_instantiation() -> None:
    template = QubitHorizontalBorders()
    numpy.testing.assert_array_equal(
        template.instantiate(2),
        [
            [1, 5, 6, 5, 6, 2],
            [3, 7, 8, 7, 8, 4],
        ],
    )
    numpy.testing.assert_array_equal(
        template.instantiate(4),
        [
            [1, 5, 6, 5, 6, 5, 6, 5, 6, 2],
            [3, 7, 8, 7, 8, 7, 8, 7, 8, 4],
        ],
    )


def test_qubit_vertical_borders_template_instantiation() -> None:
    template = QubitVerticalBorders()
    numpy.testing.assert_array_equal(
        template.instantiate(2),
        [
            [1, 2],
            [5, 7],
            [6, 8],
            [5, 7],
            [6, 8],
            [3, 4],
        ],
    )
    numpy.testing.assert_array_equal(
        template.instantiate(4),
        [
            [1, 2],
            [5, 7],
            [6, 8],
            [5, 7],
            [6, 8],
            [5, 7],
            [6, 8],
            [5, 7],
            [6, 8],
            [3, 4],
        ],
    )


def test_qubit_4_way_junction_template_instantiation() -> None:
    template = QubitSpatialJunctionTemplate()

    expected_warning_message = (
        "Instantiating Qubit4WayJunctionTemplate with k=1. The "
        "instantiation array returned will not have any plaquette indexed "
        "9, which might break other parts of the library."
    )
    with pytest.warns(TQECWarning, match=expected_warning_message):
        numpy.testing.assert_array_equal(
            template.instantiate(1),
            [
                [1, 5, 6, 2],
                [7, 10, 11, 12],
                [8, 11, 10, 13],
                [3, 14, 15, 4],
            ],
        )
    numpy.testing.assert_array_equal(
        template.instantiate(2),
        [
            [1, 5, 6, 5, 6, 2],
            [7, 10, 11, 10, 11, 12],
            [8, 11, 10, 11, 9, 13],
            [7, 9, 11, 10, 11, 12],
            [8, 11, 10, 11, 10, 13],
            [3, 14, 15, 14, 15, 4],
        ],
    )
