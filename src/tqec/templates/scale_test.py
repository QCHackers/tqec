import pytest

from tqec.exceptions import TQECException
from tqec.templates.scale import LinearFunction, PiecewiseLinearFunction


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

    intervals = list(pwl.intervals)
    assert len(intervals) == 3
    assert intervals[0][0] == float("-inf")
    assert intervals[0][1] == intervals[1][0] == 4.0
    assert intervals[1][1] == intervals[2][0] == 10.0
    assert intervals[2][1] == float("inf")

    pwl = PiecewiseLinearFunction.from_linear_function(a)
    intervals = list(pwl.intervals)
    assert len(intervals) == 1
    assert intervals[0][0] == float("-inf")
    assert intervals[0][1] == float("inf")


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
