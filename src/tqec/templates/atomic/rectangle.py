import typing as ty

import numpy
from tqec.exceptions import TQECException
from tqec.position import Shape2D
from tqec.templates.atomic.base import AtomicTemplate
from tqec.templates.scale import Dimension


class AlternatingRectangleTemplate(AtomicTemplate):
    def __init__(
        self,
        width: Dimension,
        height: Dimension,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        """Implements an atomic rectangular template with alternating plaquettes.

        ## Example
        The following code:
        ```python
        from tqec.templates.scale import Dimension
        from tqec.templates.atomic.rectangle import AlternatingRectangleTemplate
        from tqec.display import display_template

        width = Dimension(4, scaling_function=lambda k: 2*k)
        height = Dimension(6, scaling_function=lambda k: 3*k)
        template = AlternatingRectangleTemplate(width, height)

        print("Non-scaled template:")
        display_template(template)
        print("Scaled template:")
        display_template(template.scale_to(1))
        ```
        outputs
        ```text
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
        ```
        :param width: rectangle width.
        :param height: rectangle height.
        :param default_x_increment: default increment in the x direction between two plaquettes.
        :param default_y_increment: default increment in the y direction between two plaquettes.
        """

        super().__init__(default_x_increment, default_y_increment)
        self._width = width
        self._height = height

    def instantiate(self, p1: int, p2: int, *_: int) -> numpy.ndarray:
        ret = numpy.zeros(self.shape.to_numpy_shape(), dtype=int)
        odd = slice(0, None, 2)
        even = slice(1, None, 2)
        ret[even, even] = p1
        ret[odd, odd] = p1
        ret[even, odd] = p2
        ret[odd, even] = p2
        return ret

    def scale_to(self, k: int) -> "AlternatingRectangleTemplate":
        self._width.scale_to(k)
        self._height.scale_to(k)
        return self

    @property
    def shape(self) -> Shape2D:
        return Shape2D(self._width.value, self._height.value)

    def to_dict(self) -> dict[str, ty.Any]:
        return super().to_dict() | {
            "width": self._width.to_dict(),
            "height": self._height.to_dict(),
        }

    @property
    def expected_plaquettes_number(self) -> int:
        return 2


class RawRectangleTemplate(AtomicTemplate):
    def __init__(
        self,
        indices: list[list[int]],
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        """
        Implements an atomic rectangular template with user-provided
        plaquette distribution.

        User-provided `indices` defines the width and height of the template.
        The integers in `indices` will be used to index the `plaquette_indices`
        provided to the `instantiate` method. The maximum integer in `indices`
        is the expected number of plaquettes to instantiate the template.

        ## Example
        The following code:
        ```python
        from tqec.templates.atomic.rectangle import RawRectangleTemplate
        from tqec.display import display_template

        one_plaquette = RawRectangleTemplate([[0]])
        template = RawRectangleTemplate([[2, 1], [1, 1], [0, 3]])

        print("One plaquette:")
        display_template(one_plaquette)
        print("Full template:")
        display_template(template)
        ```
        outputs
        ```text
        One plaquette:
        1
        Full template:
        3  2
        2  2
        1  4
        ```
        :param indices: 2-dimensional list of indices that will be used to index the
            plaquette_indices provided to the `instantiate` method.
        :param default_x_increment: default increment in the x direction between two plaquettes.
        :param default_y_increment: default increment in the y direction between two plaquettes.
        """
        super().__init__(default_x_increment, default_y_increment)
        if len(set(len(line) for line in indices)) > 1:
            raise TQECException("All lines should have the same length.")
        self._indices = indices

    def instantiate(self, *plaquette_indices: int) -> numpy.ndarray:
        try:
            # Use numpy indexing to instantiate the raw values.
            plaquette_indices_array = numpy.array(plaquette_indices, dtype=int)
            indices = numpy.array(self._indices, dtype=int)
            return plaquette_indices_array[indices]
        except IndexError:
            raise TQECException(
                "RawRectangleTemplate instances should be constructed with 2-dimensional arrays "
                "that contain indices that will index the plaquette_indices provided to "
                "this method. The bigest index you provided at this instance creation is "
                f"{max(max(index) for index in self._indices)} "
                f"but you provided only {len(plaquette_indices)} plaquette indices "
                "when calling this method."
            )

    def scale_to(self, _: int) -> "RawRectangleTemplate":
        return self

    @property
    def shape(self) -> Shape2D:
        if not self._indices:
            return Shape2D(0, 0)
        else:
            return Shape2D(len(self._indices[0]), len(self._indices))

    def to_dict(self) -> dict[str, ty.Any]:
        return super().to_dict() | {"indices": self._indices}

    @property
    def expected_plaquettes_number(self) -> int:
        return max(max(line) for line in self._indices) + 1
