import numpy
import pytest

from tqec.exceptions import TQECException
from tqec.templates.subtemplates import (
    UniqueSubTemplates,
    get_spatially_distinct_subtemplates,
)


def test_unique_subtemplates_creation() -> None:
    UniqueSubTemplates(numpy.array([[0, 1], [0, 1]]), {1: numpy.array([[1]])})
    with pytest.raises(
        TQECException,
        match=(
            "^Found an index in subtemplate_indices that does "
            "not correspond to a valid subtemplate.$"
        ),
    ):
        UniqueSubTemplates(numpy.array([[0, 1], [0, 1]]), {2: numpy.array([[1]])})
    with pytest.raises(
        TQECException, match="^There should be no subtemplate for the 0 index.$"
    ):
        UniqueSubTemplates(
            numpy.array([[0, 1], [0, 1]]), {0: numpy.array([[]]), 1: numpy.array([[1]])}
        )
    with pytest.raises(
        TQECException,
        match=(
            "^Subtemplate shapes are expected to be square. "
            r"Found the shape \(1, 3\) that is not a square.$"
        ),
    ):
        UniqueSubTemplates(numpy.array([[0, 1], [0, 1]]), {1: numpy.array([[1, 0, 1]])})
    with pytest.raises(
        TQECException,
        match=(
            "^Subtemplate shapes are expected to be squares with an "
            "odd size length. Found size length 2.$"
        ),
    ):
        UniqueSubTemplates(
            numpy.array([[0, 1], [0, 1]]),
            {1: numpy.array([[1, 0], [1, 0]])},
        )
    with pytest.raises(
        TQECException,
        match=(
            "^All the subtemplates should have the exact same shape. "
            "Found one with a differing shape.$"
        ),
    ):
        UniqueSubTemplates(
            numpy.array([[0, 1], [2, 1]]),
            {
                1: numpy.array([[1, 0, 1], [1, 0, 1], [1, 0, 1]]),
                2: numpy.array([[1]]),
            },
        )


def test_unique_subtemplates_manhattan_radius() -> None:
    for radius in range(10):
        assert (
            UniqueSubTemplates(
                numpy.ones((5 * radius, 5 * radius), dtype=numpy.int_),
                {1: numpy.ones((2 * radius + 1, 2 * radius + 1), dtype=numpy.int_)},
            ).manhattan_radius
            == radius
        )


def test_get_spatially_distinct_subtemplates() -> None:
    for radius in range(10):
        assert get_spatially_distinct_subtemplates(
            numpy.array([[1]]), manhattan_radius=radius, avoid_zero_plaquettes=True
        ) == UniqueSubTemplates(
            numpy.array([[1]]),
            {1: numpy.pad(numpy.array([[1]]), radius, "constant", constant_values=0)},
        )
    assert get_spatially_distinct_subtemplates(
        numpy.array([[1, 2], [3, 4]]), manhattan_radius=0, avoid_zero_plaquettes=True
    ) == UniqueSubTemplates(
        numpy.array([[1, 2], [3, 4]]),
        {i: numpy.array([[i]]) for i in range(1, 5)},
    )
    assert get_spatially_distinct_subtemplates(
        numpy.array([[1, 2], [3, 4]]), manhattan_radius=1, avoid_zero_plaquettes=True
    ) == UniqueSubTemplates(
        numpy.array([[1, 2], [3, 4]]),
        {
            1: numpy.array([[0, 0, 0], [0, 1, 2], [0, 3, 4]]),
            2: numpy.array([[0, 0, 0], [1, 2, 0], [3, 4, 0]]),
            3: numpy.array([[0, 1, 2], [0, 3, 4], [0, 0, 0]]),
            4: numpy.array([[1, 2, 0], [3, 4, 0], [0, 0, 0]]),
        },
    )
    assert get_spatially_distinct_subtemplates(
        numpy.array([[0, 0], [1, 0]]), manhattan_radius=1, avoid_zero_plaquettes=True
    ) == UniqueSubTemplates(
        numpy.array([[0, 0], [1, 0]]),
        {1: numpy.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]])},
    )
    assert get_spatially_distinct_subtemplates(
        numpy.array([[0, 0], [1, 0]]), manhattan_radius=1, avoid_zero_plaquettes=False
    ) == UniqueSubTemplates(
        numpy.array([[1, 2], [3, 4]]),
        {
            1: numpy.array([[0, 0, 0], [0, 0, 0], [0, 1, 0]]),
            2: numpy.array([[0, 0, 0], [0, 0, 0], [1, 0, 0]]),
            3: numpy.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]]),
            4: numpy.array([[0, 0, 0], [1, 0, 0], [0, 0, 0]]),
        },
    )
