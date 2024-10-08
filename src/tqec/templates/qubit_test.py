import numpy
import pytest

from tqec.exceptions import TQECException, TQECWarning
from tqec.scale import LinearFunction, Scalable2D
from tqec.templates.enums import TemplateSide
from tqec.templates.qubit import (
    Qubit4WayJunctionTemplate,
    QubitHorizontalBorders,
    QubitTemplate,
    QubitVerticalBorders,
)


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


def test_qubit_4_way_junction_template_instantiation() -> None:
    template = Qubit4WayJunctionTemplate(k=1)

    expected_warning_message = (
        "Instantiating Qubit4WayJunctionTemplate with k=1. The "
        "instantiation array returned will not have any plaquette indexed "
        "9, which might break other parts of the library."
    )
    with pytest.warns(TQECWarning, match=expected_warning_message):
        numpy.testing.assert_array_equal(
            template.instantiate(),
            [
                [1, 5, 6, 2],
                [7, 10, 11, 12],
                [8, 11, 10, 13],
                [3, 14, 15, 4],
            ],
        )
    template.scale_to(2)
    numpy.testing.assert_array_equal(
        template.instantiate(),
        [
            [1, 5, 6, 5, 6, 2],
            [7, 10, 11, 10, 11, 12],
            [8, 11, 10, 11, 9, 13],
            [7, 9, 11, 10, 11, 12],
            [8, 11, 10, 11, 10, 13],
            [3, 14, 15, 14, 15, 4],
        ],
    )


def test_qubit_plaquette_sides() -> None:
    # 1  5  6  5  6  2
    # 7  9 10  9 10 11
    # 8 10  9 10  9 12
    # 7  9 10  9 10 11
    # 8 10  9 10  9 12
    # 3 13 14 13 14  4
    template = QubitTemplate()
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP_LEFT]) == [1]
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP]) == [5, 6]
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP_RIGHT]) == [2]
    assert template.get_plaquette_indices_on_sides([TemplateSide.LEFT]) == [7, 8]
    assert template.get_plaquette_indices_on_sides([TemplateSide.RIGHT]) == [11, 12]
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM_LEFT]) == [3]
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM]) == [13, 14]
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM_RIGHT]) == [4]


def test_qubit_vertical_border_plaquette_sides() -> None:
    # 1 2
    # 5 7
    # 6 8
    # 5 7
    # 6 8
    # 3 4
    template = QubitVerticalBorders()
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP_LEFT]) == [1]
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP]) == []
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP_RIGHT]) == [2]
    assert template.get_plaquette_indices_on_sides([TemplateSide.LEFT]) == [5, 6]
    assert template.get_plaquette_indices_on_sides([TemplateSide.RIGHT]) == [7, 8]
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM_LEFT]) == [3]
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM]) == []
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM_RIGHT]) == [4]


def test_qubit_horizontal_border_plaquette_sides() -> None:
    # 1 5 6 5 6 2
    # 3 7 8 7 8 4
    template = QubitHorizontalBorders()
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP_LEFT]) == [1]
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP]) == [5, 6]
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP_RIGHT]) == [2]
    assert template.get_plaquette_indices_on_sides([TemplateSide.LEFT]) == []
    assert template.get_plaquette_indices_on_sides([TemplateSide.RIGHT]) == []
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM_LEFT]) == [3]
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM]) == [7, 8]
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM_RIGHT]) == [4]


def test_qubit_4way_junction_plaquette_sides() -> None:
    # 1  5  6  5  6  5  6  5  6  2
    # 7 10 11 10 11 10 11 10 11 12
    # 8 11 10 11 10 11 10 11  9 13
    # 7  9 11 10 11 10 11  9 11 12
    # 8 11  9 11 10 11  9 11  9 13
    # 7  9 11  9 11 10 11  9 11 12
    # 8 11  9 11 10 11 10 11  9 13
    # 7  9 11 10 11 10 11 10 11 12
    # 8 11 10 11 10 11 10 11 10 13
    # 3 14 15 14 15 14 15 14 15  4
    template = Qubit4WayJunctionTemplate()
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP_LEFT]) == [1]
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP]) == [5, 6]
    assert template.get_plaquette_indices_on_sides([TemplateSide.TOP_RIGHT]) == [2]
    assert template.get_plaquette_indices_on_sides([TemplateSide.LEFT]) == [7, 8]
    assert template.get_plaquette_indices_on_sides([TemplateSide.RIGHT]) == [12, 13]
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM_LEFT]) == [3]
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM]) == [14, 15]
    assert template.get_plaquette_indices_on_sides([TemplateSide.BOTTOM_RIGHT]) == [4]
