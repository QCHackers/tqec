import typing as ty

import numpy
from tqec.enums import CornerPositionEnum
from tqec.position import Shape2D
from tqec.templates.atomic.rectangle import AlternatingRectangleTemplate
from tqec.templates.base import Template
from tqec.templates.scale import Dimension


class AlternatingSquareTemplate(AlternatingRectangleTemplate):
    def __init__(
        self,
        dimension: Dimension,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        """Implements an atomic square template with alternating plaquettes.

        Args:
            dimension: width and height of the square template.
            default_x_increment: default increment in the x direction between two plaquettes.
            default_y_increment: default increment in the y direction between two plaquettes.

        Example:
            The following code:
            .. code-block:: python

                from tqec.templates.scale import Dimension
                from tqec.templates.atomic.rectangle import AlternatingSquareTemplate
                from tqec.display import display_template

                dim = Dimension(2, scaling_function=lambda k: 2*k)
                template = AlternatingSquareTemplate(dim)

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
        CornerPositionEnum.UPPER_RIGHT: lambda arr: arr[
            :, numpy.arange(arr.shape[0])[::-1]
        ],
        # Exchange line i and line n - i
        CornerPositionEnum.LOWER_LEFT: lambda arr: arr[
            numpy.arange(arr.shape[0])[::-1], :
        ],
        # Exchange BOTH (line i and line n - i) and (column i and column n - i)
        CornerPositionEnum.LOWER_RIGHT: lambda arr: arr[
            numpy.arange(arr.shape[0])[::-1], numpy.arange(arr.shape[0])[::-1]
        ],
    }

    def __init__(
        self,
        dimension: Dimension,
        corner_position: CornerPositionEnum,
        top_plaquettes_on_diagonal: bool = False,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        super().__init__(
            default_x_increment=default_x_increment,
            default_y_increment=default_y_increment,
        )
        self._dimension = dimension
        self._corner_position = corner_position
        self._top_plaquettes_on_diagonal = top_plaquettes_on_diagonal

    def instantiate(self, plaquette_indices: ty.Sequence[int]) -> numpy.ndarray:
        self._check_plaquette_number(plaquette_indices)
        p1, p2, p1_flipped, p2_flipped, corner_plaquette = plaquette_indices[:5]
        ret = numpy.zeros(self.shape.to_numpy_shape(), dtype=int)
        # Fill ret as if it was in the upper-left corner and then correct
        ret[0, 0] = corner_plaquette
        dimension = self._dimension.value
        for i in range(dimension):
            for j in range(dimension):
                if i == j == 0:
                    ret[i, j] = corner_plaquette
                elif i > j or (self._top_plaquettes_on_diagonal and i == j):
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
        """Returns the number of plaquettes expected from the `instantiate` method.

        :returns: the number of plaquettes expected from the `instantiate` method.
        """
        return 5

    def scale_to(self, k: int) -> "AlternatingCornerSquareTemplate":
        """Scales self to the given scale k.

        The scale k of a **scalable template** is defined to be **half** the dimension/size
        of the **scalable axis** of the template. For example, a scalable 4x4 square T has a
        scale of 2 for both its axis. This means the dimension/size of the scaled axis is
        enforced to be even, which avoids some invalid configuration of the template.

        Note that this function scales to INLINE, so the instance on which it is called is
        modified in-place AND returned.

        :param k: the new scale of the template.
        :returns: self, once scaled.
        """
        self._dimension.scale_to(k)
        return self

    @property
    def shape(self) -> Shape2D:
        return Shape2D(self._dimension.value, self._dimension.value)
