import pytest

from tqec.exceptions import TQECException
from tqec.templates.atomic.square import AlternatingSquareTemplate
from tqec.templates.base import TemplateWithIndices
from tqec.templates.scale import LinearFunction


@pytest.fixture
def square_template():
    return AlternatingSquareTemplate(LinearFunction(2))


def test_template_with_indices_creation(square_template):
    twi = TemplateWithIndices(square_template, [1, 2])
    assert twi.indices == [1, 2]
    assert twi.template == square_template


def test_template_with_indices_creation_wrong_number_of_indices(square_template):
    with pytest.raises(TQECException):
        TemplateWithIndices(square_template, [])
    with pytest.raises(TQECException):
        TemplateWithIndices(square_template, [1])
    with pytest.raises(TQECException):
        TemplateWithIndices(square_template, [2, 4, 1])


def test_template_with_negative_indices_creation(square_template):
    with pytest.raises(TQECException):
        TemplateWithIndices(square_template, [-1, 0])
