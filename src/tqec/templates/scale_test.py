import pytest
from tqec.templates.scale import Dimension, FixedDimension, LinearFunction


@pytest.mark.parametrize(
    "slope,offset", [(0, 0), (2, 0), (1, 0), (0, 4), (-1, 5), (2, -1)]
)
def test_linear_function(slope: int, offset: int):
    f = LinearFunction(slope, offset)
    assert f(10) == slope * 10 + offset
    assert f(1) == slope + offset
    assert f(0) == offset
    assert f(-4) == slope * -4 + offset


def test_dimension_init():
    dim = Dimension(5, LinearFunction())
    assert dim.value == 5


def test_dimension_default_scaling():
    dim = Dimension(2, scaling_function=LinearFunction(2))
    dim.scale_to(3)
    assert dim.value == 2 * 3


def test_dimension_scaling():
    scaling_func = LinearFunction(3, 4)

    dim = Dimension(2, scaling_func)
    dim.scale_to(4)
    assert dim.value == scaling_func(4)
    assert dim.scale_to(19).value == scaling_func(19)


def test_fixed_dimension():
    dim = FixedDimension(3)
    assert dim.value == 3
    assert dim.scale_to(10).value == 3
    assert dim.scale_to(421).value == 3
