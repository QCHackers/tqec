import pytest

from tqec.templates.interval import Interval, Intervals, R_intervals
from tqec.templates.scale import LinearFunction, ScalableInterval


@pytest.mark.parametrize(
    "slope,offset", [(0, 0), (2, 0), (1, 0), (0, 4), (-1, 5), (2, -1)]
)
def test_linear_function(slope: int, offset: int) -> None:
    f = LinearFunction(slope, offset)
    assert f(10) == slope * 10 + offset
    assert f(1) == slope + offset
    assert f(0) == offset
    assert f(-4) == slope * -4 + offset


def test_linear_function_operators() -> None:
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)
    assert (a + b)(10) == a(10) + b(10)
    assert (a - b)(3) == a(3) - b(3)
    assert (3 * a)(54) == 3 * a(54)
    assert (a * 3)(54) == 3 * a(54)


def test_intersection() -> None:
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)
    intersection = a.intersection(b)
    assert intersection is not None
    assert abs(intersection - 4) < 1e-8

    intersection = a.intersection(a)
    assert intersection is None


def test_linear_function_comparison() -> None:
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)

    assert (a < b) == Interval(
        4.0, float("inf"), start_excluded=True, end_excluded=True
    )
    assert (a < a).is_empty()
    assert (a <= b) == Interval(
        4.0, float("inf"), start_excluded=False, end_excluded=True
    )
    assert (a <= a) == Interval(
        float("-inf"), float("inf"), start_excluded=True, end_excluded=True
    )


def test_scalable_interval_creation() -> None:
    ScalableInterval(LinearFunction(2), LinearFunction(2, 2))


def test_scalable_interval_non_empty_on_colinear() -> None:
    sint = ScalableInterval(LinearFunction(2), LinearFunction(2, 2))
    assert sint.non_empty_on() == R_intervals

    sint = ScalableInterval(LinearFunction(2), LinearFunction(2))
    assert sint.non_empty_on() == Intervals([])


def test_scalable_interval_non_empty_on() -> None:
    sint = ScalableInterval(LinearFunction(2), LinearFunction(3))
    assert sint.non_empty_on() == Intervals(
        [Interval(0, float("inf"), start_excluded=True, end_excluded=True)]
    )
