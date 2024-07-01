import numpy

from tqec.templates.atomic.rectangle import RawRectangleTemplate
from tqec.templates.constructions.grid import TemplateGrid
from tqec.templates.constructions.qubit import DenseQubitSquareTemplate
from tqec.templates.scale import LinearFunction


def test_grid_simple():
    template = RawRectangleTemplate([[0]])
    grid = TemplateGrid(2, 2, template)

    assert grid.expected_plaquettes_number == 4
    arr = grid.instantiate([1, 2, 3, 4])
    numpy.testing.assert_allclose(arr, [[1, 2], [3, 4]])

    grid.scale_to(18)
    assert grid.expected_plaquettes_number == 4
    arr = grid.instantiate([1, 2, 3, 4])
    numpy.testing.assert_allclose(arr, [[1, 2], [3, 4]])


def test_grid_qubits():
    template = DenseQubitSquareTemplate(LinearFunction(0, 2), k=2)
    assert template.expected_plaquettes_number == 14
    template_arr = template.instantiate(list(range(1, 15)))

    grid = TemplateGrid(3, 2, template)
    assert grid.expected_plaquettes_number == 14 * 3 * 2
    grid_arr = grid.instantiate(list(range(1, 1 + 14 * 2 * 3)))

    plaquettes_per_template = template.expected_plaquettes_number
    expected_arr = numpy.vstack(
        (
            numpy.hstack((template_arr, template_arr + plaquettes_per_template)),
            numpy.hstack(
                (
                    template_arr + 2 * plaquettes_per_template,
                    template_arr + 3 * plaquettes_per_template,
                )
            ),
            numpy.hstack(
                (
                    template_arr + 4 * plaquettes_per_template,
                    template_arr + 5 * plaquettes_per_template,
                )
            ),
        )
    )
    assert grid_arr.shape == expected_arr.shape
    numpy.testing.assert_allclose(grid_arr, expected_arr)
