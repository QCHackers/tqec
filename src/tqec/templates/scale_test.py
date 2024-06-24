import pytest

from tqec.exceptions import TQECException
from tqec.templates.scale import LinearFunction


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


def test_linear_function_invert():
    a = LinearFunction(2, 5)
    assert a.invert(a(11)) == 11


def test_linear_function_constant_invert():
    a = LinearFunction(0, 5)
    with pytest.raises(TQECException):
        a.invert(5)


def test_linear_function_non_exact_invert():
    a = LinearFunction(2, 0)
    with pytest.raises(TQECException):
        a.invert(5)
