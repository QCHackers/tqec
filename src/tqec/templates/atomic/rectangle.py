import typing as ty

import numpy

from tqec.enums import TemplateOrientation
from tqec.exceptions import TQECException
from tqec.position import Shape2D
from tqec.templates.base import Template
from tqec.templates.scale import LinearFunction


class AlternatingRectangleTemplate(Template):
    def __init__(
        self,
        width: LinearFunction,
        height: LinearFunction,
        k: int = 2,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        """Implements an atomic rectangular template with alternating plaquettes.

        Args:
            width: rectangle width.
            height: rectangle height.
            k: initial value for the scaling parameter.
            default_x_increment: default increment in the x direction between two plaquettes.
            default_y_increment: default increment in the y direction between two plaquettes.

        Example:
            The following code:
            .. code-block:: python

                from tqec.templates.scale import LinearFunction
                from tqec.templates.atomic.rectangle import AlternatingRectangleTemplate
                from tqec.display import display_template

                width = LinearFunction(2, 0)
                height = LinearFunction(3, 0)
                template = AlternatingRectangleTemplate(width, height)

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
                1  2  1  2
                2  1  2  1
                Scaled template:
                1  2
                2  1
                1  2
        """

        super().__init__(k, default_x_increment, default_y_increment)
        self._width = width
        self._height = height

    def instantiate(self, plaquette_indices: ty.Sequence[int]) -> numpy.ndarray:
        self._check_plaquette_number(plaquette_indices, 2)
        p1, p2 = plaquette_indices[:2]
        ret = numpy.zeros(self.shape.to_numpy_shape(), dtype=int)
        odd = slice(0, None, 2)
        even = slice(1, None, 2)
        ret[even, even] = p1
        ret[odd, odd] = p1
        ret[even, odd] = p2
        ret[odd, even] = p2
        return ret

    @property
    def shape(self) -> Shape2D:
        return Shape2D(self._width(self.k), self._height(self.k))

    @property
    def expected_plaquettes_number(self) -> int:
        return 2

    def get_midline_plaquettes(
        self, orientation: TemplateOrientation = TemplateOrientation.HORIZONTAL
    ) -> list[tuple[int, int]]:
        midline_shape, iteration_shape = self.shape.x, self.shape.y
        if orientation == TemplateOrientation.VERTICAL:
            midline_shape, iteration_shape = iteration_shape, midline_shape

        if midline_shape % 2 == 1:
            raise TQECException(
                "Midline is not defined for odd "
                + f"{'height' if orientation == TemplateOrientation.HORIZONTAL else 'width'}."
            )
        midline = midline_shape // 2 - 1
        if orientation == TemplateOrientation.VERTICAL:
            return [(row, midline) for row in range(iteration_shape)]
        return [(midline, column) for column in range(iteration_shape)]


@ty.final
class RawRectangleTemplate(Template):
    def __init__(
        self,
        indices: list[list[int]],
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        """
        Implements an atomic rectangular template with user-provided
        plaquette distribution.

        User-provided ``indices`` defines the width and height of the template.
        The integers in ``indices`` will be used to index the ``plaquette_indices``
        provided to the ``instantiate`` method. The maximum integer in ``indices``
        is used to compute the expected number of plaquettes to instantiate the
        template, that is ``1 + max(max(line) for line in indices)``.`

        This template cannot be inherited from for the moment. This is to avoid
        potential mistakes when sub-classing this class and overriding some of its
        methods.

        Args:
            indices: 2-dimensional list of indices that will be used to index the
                plaquette_indices provided to the ``instantiate`` method. Should contain
                a contiguous set of positive indices starting from 0 (i.e., the set of
                integer indices present should be equal to ``range(n)`` for some ``n``).
            default_x_increment: default increment in the x direction between two plaquettes.
            default_y_increment: default increment in the y direction between two plaquettes.

        Example:
            The following code:
            .. code-block:: python

                from tqec.templates.atomic.rectangle import RawRectangleTemplate
                from tqec.display import display_template

                one_plaquette = RawRectangleTemplate([[0]])
                template = RawRectangleTemplate([[2, 1], [1, 1], [0, 3]])

                print("One plaquette:")
                display_template(one_plaquette)
                print("Full template:")
                display_template(template)

            outputs ::

                One plaquette:
                1
                Full template:
                3  2
                2  2
                1  4
        """
        super().__init__(0, default_x_increment, default_y_increment)
        if not indices or not indices[0]:
            raise TQECException(
                f"You should provide at least one index to {self.__class__.__name__}."
            )
        line_lens = set(len(line) for line in indices)
        if len(line_lens) > 1:
            raise TQECException(
                f"The 2-dimensional array provided to {self.__class__.__name__} should "
                "be rectangular. Please provide an array with equally-sized rows."
            )
        all_indices: set[int] = set().union(*[set(line) for line in indices])
        expected_indices = set(range(len(all_indices)))
        missing_expected_indices = expected_indices.difference(all_indices)
        if missing_expected_indices:
            min_index = min(min(row) for row in indices)
            max_index = max(max(row) for row in indices)
            raise TQECException(
                f"{self.__class__.__name__} is expecting a 2-dimensional array of "
                f"CONTIGUOUS indices starting at 0. You provided indices between "
                f"{min_index} and {max_index} but the following indices were "
                f"missing: {missing_expected_indices}."
            )
        self._indices = indices

    def instantiate(self, plaquette_indices: ty.Sequence[int]) -> numpy.ndarray:
        # Warning: self.expected_plaquettes_number is only guaranteed to be correct
        #          here because RawRectangleTemplate is annotated as final.
        self._check_plaquette_number(plaquette_indices, self.expected_plaquettes_number)
        try:
            # Use numpy indexing to instantiate the raw values.
            plaquette_indices_array = numpy.array(plaquette_indices, dtype=int)
            indices = numpy.array(self._indices, dtype=int)
            return plaquette_indices_array[indices]
        except IndexError as ex:
            raise TQECException(
                "RawRectangleTemplate instances should be constructed with 2-dimensional arrays "
                "that contain indices that will index the plaquette_indices provided to "
                "this method. The biggest index you provided at this instance creation is "
                f"{max(max(index) for index in self._indices)} "
                f"but you provided only {len(plaquette_indices)} plaquette indices "
                "when calling this method."
            ) from ex

    def scale_to(self, _: int) -> "RawRectangleTemplate":
        return self

    @property
    def shape(self) -> Shape2D:
        return Shape2D(len(self._indices[0]), len(self._indices))

    @property
    def expected_plaquettes_number(self) -> int:
        return max(max(line) for line in self._indices) + 1

    def get_midline_plaquettes(
        self, orientation: TemplateOrientation = TemplateOrientation.HORIZONTAL
    ) -> list[tuple[int, int]]:
        midline_shape, iteration_shape = self.shape.x, self.shape.y
        if orientation == TemplateOrientation.VERTICAL:
            midline_shape, iteration_shape = iteration_shape, midline_shape

        if midline_shape % 2 == 1:
            raise TQECException(
                "Midline is not defined for odd "
                + f"{'height' if orientation == TemplateOrientation.HORIZONTAL else 'width'}."
            )
        midline = midline_shape // 2 - 1
        if orientation == TemplateOrientation.VERTICAL:
            return [(row, midline) for row in range(iteration_shape)]
        return [(midline, column) for column in range(iteration_shape)]
