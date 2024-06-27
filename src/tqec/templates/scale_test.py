import pytest

from tqec.templates.interval import Interval, Intervals
from tqec.templates.scale import (
    LinearFunction,
    PiecewiseLinearFunction,
    intervals_from_separators,
)


@pytest.mark.parametrize(
    "slope,offset", [(0, 0), (2, 0), (1, 0), (0, 4), (-1, 5), (2, -1)]
)
def test_linear_function(slope: int, offset: int):
    f = LinearFunction(slope, offset)
    assert f(10) == slope * 10 + offset
    assert f(1) == slope + offset
    assert f(0) == offset
    assert f(-4) == slope * -4 + offset


def test_linear_function_operators():
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)
    assert (a + b)(10) == a(10) + b(10)
    assert (a - b)(3) == a(3) - b(3)
    assert (3 * a)(54) == 3 * a(54)
    assert (a * 3)(54) == 3 * a(54)


def test_intersection():
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)
    intersection = a.intersection(b)
    assert intersection is not None
    assert abs(intersection - 4) < 1e-8

    intersection = a.intersection(a)
    assert intersection is None


def test_linear_function_comparison():
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)

    assert (a < b) == Interval(4.0, float("inf"))
    assert (a < a).is_empty()
    assert (a <= b) == Interval(4.0, float("inf"))
    assert (a <= a) == Interval(float("-inf"), float("inf"))


def test_from_linear_function():
    linear_func = LinearFunction(2, 5)
    pwl_func = PiecewiseLinearFunction.from_linear_function(linear_func)

    for i in range(100):
        assert linear_func(i) == pwl_func(i)


def test_piecewise_operators():
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)
    a_pwl, b_pwl = (
        PiecewiseLinearFunction.from_linear_function(a),
        PiecewiseLinearFunction.from_linear_function(b),
    )
    assert (a + b)(10) == (a_pwl + b_pwl)(10) == a_pwl(10) + b_pwl(10)
    assert (a - b)(3) == (a_pwl - b_pwl)(3) == a_pwl(3) - b_pwl(3)
    assert (3 * a)(54) == (3 * a_pwl)(54) == 3 * a_pwl(54)
    assert (a * 3)(54) == (a_pwl * 3)(54) == 3 * a_pwl(54)


def test_piecewise_construction():
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)
    pwl = PiecewiseLinearFunction([4], [a, b])

    for i in range(0, 5):
        assert pwl(i) == a(i)
    for i in range(4, 10):
        assert pwl(i) == b(i)

    pwl_reversed = PiecewiseLinearFunction([4], [b, a])

    for i in range(0, 5):
        assert pwl_reversed(i) == b(i)
    for i in range(4, 10):
        assert pwl_reversed(i) == a(i)


def test_piecewise_intervals():
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)
    pwl = PiecewiseLinearFunction([4, 10], [a, b, a])

    intervals = list(intervals_from_separators(pwl.separators))
    assert len(intervals) == 3
    assert intervals[0].start == float("-inf")
    assert intervals[0].end == intervals[1].start == 4.0
    assert intervals[1].end == intervals[2].start == 10.0
    assert intervals[2].end == float("inf")

    pwl = PiecewiseLinearFunction.from_linear_function(a)
    intervals = list(intervals_from_separators(pwl.separators))
    assert len(intervals) == 1
    assert intervals[0].start == float("-inf")
    assert intervals[0].end == float("inf")


def test_simplifiable_piecewise():
    a = LinearFunction(2, 5)
    pwl = PiecewiseLinearFunction.from_linear_function(a)
    simplified_pwl = pwl.simplify()

    assert len(simplified_pwl.separators) == 0
    assert len(simplified_pwl.functions) == 1
    assert simplified_pwl.functions[0] == a


def test_piecewise_min():
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)
    a_pwl, b_pwl = (
        PiecewiseLinearFunction.from_linear_function(a),
        PiecewiseLinearFunction.from_linear_function(b),
    )

    minab = PiecewiseLinearFunction.min(a_pwl, b_pwl).simplify()
    assert minab.separators == [a.intersection(b)]
    assert minab.functions == [b, a]

    c = LinearFunction(-1, 10)
    c_pwl = PiecewiseLinearFunction.from_linear_function(c)

    minabc = PiecewiseLinearFunction.min(minab, c_pwl).simplify()
    assert minabc.separators == [b.intersection(c)]
    assert minabc.functions == [b, c]


def test_piecewise_max():
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)
    a_pwl, b_pwl = (
        PiecewiseLinearFunction.from_linear_function(a),
        PiecewiseLinearFunction.from_linear_function(b),
    )

    maxab = PiecewiseLinearFunction.max(a_pwl, b_pwl).simplify()
    assert maxab.separators == [a.intersection(b)]
    assert maxab.functions == [a, b]

    c = LinearFunction(-1, 10)
    c_pwl = PiecewiseLinearFunction.from_linear_function(c)

    maxabc = PiecewiseLinearFunction.max(maxab, c_pwl).simplify()
    assert maxabc.separators == [a.intersection(c), a.intersection(b)]
    assert maxabc.functions == [c, a, b]

    d = LinearFunction(0, 10)
    d_pwl = PiecewiseLinearFunction.from_linear_function(d)

    maxabcd = PiecewiseLinearFunction.max(maxabc, d_pwl).simplify()
    assert maxabcd.separators == [
        c.intersection(d),
        d.intersection(a),
        a.intersection(b),
    ]
    assert maxabcd.functions == [c, d, a, b]


def test_piecewise_max_constant():
    a, b = LinearFunction(0, 0), LinearFunction(0, 1)
    a_pwl, b_pwl = (
        PiecewiseLinearFunction.from_linear_function(a),
        PiecewiseLinearFunction.from_linear_function(b),
    )

    maxab = PiecewiseLinearFunction.max(a_pwl, b_pwl)
    assert maxab.separators == []
    assert maxab.functions == [b]


def test_piecewiselinear_function_comparison():
    a, b = LinearFunction(2, 5), LinearFunction(3, 1)
    a_pwl, b_pwl = (
        PiecewiseLinearFunction.from_linear_function(a),
        PiecewiseLinearFunction.from_linear_function(b),
    )

    assert (a_pwl < b_pwl) == Intervals([Interval(4.0, float("inf"))])
    assert (a_pwl < a_pwl).is_empty()
    assert (a_pwl <= b_pwl) == Intervals([Interval(4.0, float("inf"))])
    assert (a_pwl <= a_pwl) == Intervals([Interval(float("-inf"), float("inf"))])

    a = LinearFunction(-1, -2)
    b = LinearFunction(1, -2)
    c = LinearFunction(1, 2)
    d = LinearFunction(-1, 2)

    ab_pwl = PiecewiseLinearFunction([0], [a, b])
    cd_pwl = PiecewiseLinearFunction([0], [c, d])

    assert (ab_pwl < cd_pwl) == Intervals([Interval(-2, 2)])
    assert (cd_pwl < ab_pwl) == Intervals(
        [Interval(float("-inf"), -2), Interval(2, float("inf"))]
    )
