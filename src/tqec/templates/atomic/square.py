import typing as ty

import numpy

from tqec.enums import CornerPositionEnum, TemplateOrientation
from tqec.exceptions import TQECException
from tqec.position import Shape2D
from tqec.templates.atomic.rectangle import AlternatingRectangleTemplate
from tqec.templates.base import Template
from tqec.templates.scale import (
    LinearFunction,
    PiecewiseLinearFunction,
    Scalable2D,
    round_or_fail,
)


class AlternatingSquareTemplate(AlternatingRectangleTemplate):
    def __init__(
        self,
        dimension: LinearFunction,
        k: int = 2,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        """Implements an atomic square template with alternating plaquettes.

        Args:
            dimension: width and height of the square template.
            k: initial value for the scaling parameter.
            default_x_increment: default increment in the x direction between two plaquettes.
            default_y_increment: default increment in the y direction between two plaquettes.

        Example:
            The following code:
            .. code-block:: python

                from tqec.templates.scale import LinearFunction
                from tqec.templates.atomic.square import AlternatingSquareTemplate
                from tqec.display import display_template

                dim = LinearFunction(2, 0)
                template = AlternatingSquareTemplate(dim, k=2)

                print("Non-scaled template:")
                display_template(template)
                print("Scaled template:")
                display_template(template.scale_to(1))

            outputs ::

                Non-scaled template:
                1  2  1  2
                2  1  2  1
                1  2  1  2
                2  1  2  1
                Scaled template:
                1  2
                2  1
        """
        super().__init__(
            dimension,
            dimension,
            k,
            default_x_increment=default_x_increment,
            default_y_increment=default_y_increment,
        )


class AlternatingCornerSquareTemplate(Template):
    """TODO: This class needs fixing, the instantiate output does not adhere to
    the convention that the first plaquette provided to the method is the top-left
    one in the resulting array."""

    _TRANSFORMATIONS: dict[
        CornerPositionEnum, ty.Callable[[numpy.ndarray], numpy.ndarray]
    ] = {
        # By arbitrary convention, this class works as if the corner was on
        # the upper-left part of the corner and corrects the generated array
        # just before returning it. This means that if the corner is effectively
        # in the upper-left part, we have nothing to do.
        CornerPositionEnum.UPPER_LEFT: lambda arr: arr,
        # Exchange column i and column n - i
        CornerPositionEnum.UPPER_RIGHT: lambda arr: arr[:, ::-1],
        # Exchange line i and line n - i
        CornerPositionEnum.LOWER_LEFT: lambda arr: arr[::-1, :],
        # Exchange BOTH (line i and line n - i) and (column i and column n - i)
        CornerPositionEnum.LOWER_RIGHT: lambda arr: arr[::-1, ::-1],
    }

    def __init__(
        self,
        dimension: LinearFunction,
        corner_position: CornerPositionEnum,
        k: int = 2,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        """Implements an atomic square corner template with alternating plaquettes.

        A corner template is a square, just like the logical qubit, but:
        - one of its corner is a special plaquette,
        - the diagonal the special corner is on splits the square in two parts
          that each have a different pair of alternating plaquettes.

        Args:
            dimension: width and height of the square template.
            corner_position: position of the special corner.
            k: initial value for the scaling parameter.
            default_x_increment: default increment in the x direction between
                two plaquettes.
            default_y_increment: default increment in the y direction between
                two plaquettes.

        Example:
            The following code:
            .. code-block:: python

                from tqec.templates.scale import LinearFunction
                from tqec.templates.atomic.square import AlternatingCornerSquareTemplate
                from tqec.display import display_template
                from tqec.enums import CornerPositionEnum

                dim = LinearFunction(2, 0)
                template = AlternatingCornerSquareTemplate(dim, CornerPositionEnum.LOWER_LEFT, k=2)

                print("Non-scaled template:")
                display_template(template)
                print("Scaled template:")
                display_template(template.scale_to(1))

            outputs ::

                Non-scaled template:
                2  1  2  3
                1  2  3  4
                2  3  4  3
                5  4  3  4
                Scaled template:
                2  3
                5  4
        """
        super().__init__(
            k=k,
            default_x_increment=default_x_increment,
            default_y_increment=default_y_increment,
        )
        self._dimension = dimension
        self._corner_position = corner_position

    def instantiate(self, plaquette_indices: ty.Sequence[int]) -> numpy.ndarray:
        self._check_plaquette_number(plaquette_indices, 5)
        p1, p2, p1_flipped, p2_flipped, corner_plaquette = plaquette_indices[:5]
        ret = numpy.zeros(self.shape.to_numpy_shape(), dtype=int)
        # Fill ret as if it was in the upper-left corner and then correct
        ret[0, 0] = corner_plaquette
        dimension = round_or_fail(self._dimension(self._k))
        for i in range(dimension):
            for j in range(dimension):
                if i == j == 0:
                    ret[i, j] = corner_plaquette
                elif i > j:
                    if (i + j) % 2 == 1:
                        ret[i, j] = p2
                    else:
                        ret[i, j] = p1
                else:
                    if (i + j) % 2 == 1:
                        ret[i, j] = p2_flipped
                    else:
                        ret[i, j] = p1_flipped
        # Correct ret and return
        return self._TRANSFORMATIONS[self._corner_position](ret)

    @property
    def expected_plaquettes_number(self) -> int:
        return 5

    @property
    def scalable_shape(self) -> Scalable2D:
        """Returns a scalable version of the template shape."""
        return Scalable2D(
            PiecewiseLinearFunction.from_linear_function(self._dimension),
            PiecewiseLinearFunction.from_linear_function(self._dimension),
        )

    def get_midline_plaquettes(
        self, orientation: TemplateOrientation = TemplateOrientation.HORIZONTAL
    ) -> list[tuple[int, int]]:
        midline_shape, iteration_shape = self.shape.x, self.shape.y
        if midline_shape % 2 == 1:
            raise TQECException(
                "Midline is not defined for odd "
                + f"{'height' if orientation == TemplateOrientation.HORIZONTAL else 'width'}."
            )
        midline = midline_shape // 2 - 1
        if orientation == TemplateOrientation.VERTICAL:
            return [(row, midline) for row in range(iteration_shape)]
        return [(midline, column) for column in range(iteration_shape)]
