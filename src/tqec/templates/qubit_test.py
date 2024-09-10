import numpy
import pytest

from tqec.exceptions import TQECException
from tqec.templates.qubit import (
    Qubit4WayJunctionTemplate,
    QubitHorizontalBorders,
    QubitTemplate,
    QubitVerticalBorders,
)
from tqec.templates.scale import LinearFunction, Scalable2D


@pytest.mark.parametrize(
    "tested_class",
    [
        QubitTemplate,
        QubitHorizontalBorders,
        QubitVerticalBorders,
        Qubit4WayJunctionTemplate,
    ],
)
def test_creation(tested_class: type) -> None:
    tested_class()
    tested_class(k=10000)
    with pytest.raises(
        TQECException, match=r"^Cannot have a negative scaling parameter. Got -1.$"
    ):
        tested_class(k=-1)


def test_expected_plaquettes_number() -> None:
    assert QubitTemplate().expected_plaquettes_number == 14
    assert QubitHorizontalBorders().expected_plaquettes_number == 8
    assert QubitVerticalBorders().expected_plaquettes_number == 8
    assert Qubit4WayJunctionTemplate().expected_plaquettes_number == 15


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
    assert Qubit4WayJunctionTemplate().scalable_shape == Scalable2D(
        LinearFunction(2, 2), LinearFunction(2, 2)
    )


def test_qubit_template_instantiation() -> None:
    template = QubitTemplate(k=2)
    numpy.testing.assert_array_equal(
        template.instantiate(),
        [
            [1, 5, 6, 5, 6, 2],
            [7, 9, 10, 9, 10, 11],
            [8, 10, 9, 10, 9, 12],
            [7, 9, 10, 9, 10, 11],
            [8, 10, 9, 10, 9, 12],
            [3, 13, 14, 13, 14, 4],
        ],
    )
    template.scale_to(4)
    numpy.testing.assert_array_equal(
        template.instantiate(),
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


def test_qubit_vertical_borders_template_instantiation() -> None:
    template = QubitVerticalBorders(k=2)
    numpy.testing.assert_array_equal(
        template.instantiate(),
        [
            [1, 2],
            [5, 7],
            [6, 8],
            [5, 7],
            [6, 8],
            [3, 4],
        ],
    )
    template.scale_to(4)
    numpy.testing.assert_array_equal(
        template.instantiate(),
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


def test_qubit_horizontal_borders_template_instantiation() -> None:
    template = QubitHorizontalBorders(k=2)
    numpy.testing.assert_array_equal(
        template.instantiate(),
        [
            [1, 5, 6, 5, 6, 2],
            [3, 7, 8, 7, 8, 4],
        ],
    )
    template.scale_to(4)
    numpy.testing.assert_array_equal(
        template.instantiate(),
        [
            [1, 5, 6, 5, 6, 5, 6, 5, 6, 2],
            [3, 7, 8, 7, 8, 7, 8, 7, 8, 4],
        ],
    )
