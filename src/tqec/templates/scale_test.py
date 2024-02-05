import pytest
from tqec.exceptions import TQECException
from tqec.templates.scale import Dimension


def test_dimension_init():
    dim = Dimension(5, is_fixed=True)
    assert dim.value == 5


def test_dimension_default_scaling():
    dim = Dimension(2, scaling_function=lambda k: 2 * k)
    dim.scale_to(3)
    assert dim.value == 2 * 3


def test_dimension_raises_if_wrong_arguments():
    with pytest.raises(TQECException):
        Dimension(2)
    with pytest.raises(TQECException):
        Dimension(2, is_fixed=False)
    with pytest.raises(TQECException):
        Dimension(2, is_fixed=True, scaling_function=lambda k: 2 * k)


def test_dimension_scaling():
    def scaling_func(k: int) -> int:
        return 3 * k + 4

    dim = Dimension(2, scaling_func)
    dim.scale_to(4)
    assert dim.value == scaling_func(4)
    assert dim.scale_to(19).value == scaling_func(19)
