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
        super().__init__(default_x_increment, default_y_increment)
        self._width = width
        self._height = height

    def instanciate(self, p1: int, p2: int, *_: int) -> numpy.ndarray:
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
        super().__init__(default_x_increment, default_y_increment)
        self._indices = indices

    def instanciate(self, *plaquette_indices: int) -> numpy.ndarray:
        try:
            # Use numpy indexing to instanciate the raw values.
            plaquette_indices_array = numpy.array(plaquette_indices, dtype=int)
            indices = numpy.array(self._indices, dtype=int)
            return plaquette_indices_array[indices]
        except IndexError as e:
            e.add_note(
                "RawRectangleTemplate instances should be constructed with 2-dimensional arrays "
                "that contain indices that will index the plaquette_indices provided to "
                "this method. The bigest index you provided at this instance creation is "
                f"{max(max(index) for index in self._indices)} "
                f"but you provided only {len(plaquette_indices)} plaquette indices "
                "when calling this method."
            )
            raise e

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
        return max(max(line) for line in self._indices)


class LegacyRectangleTemplate(AlternatingRectangleTemplate):
    def __init__(
        self,
        width: int,
        height: int,
        scale_width: bool | None = None,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        if width % 2 != 0 and height % 2 != 0:
            raise TQECException(
                f"At least one of width ({width}) or height ({height}) should be even. "
                "Dimension must be even to be scalable!"
            )

        # Determine which dimension to scale
        if scale_width is None:
            scale_width = height % 2 != 0 or (width % 2 == 0 and width >= height)

        if scale_width:
            width_dim = Dimension(width, lambda k: 2 * k)
            height_dim = Dimension(height, is_fixed=True)
        else:
            width_dim = Dimension(width, is_fixed=True)
            height_dim = Dimension(height, lambda k: 2 * k)
        super().__init__(
            width_dim, height_dim, default_x_increment, default_y_increment
        )


class FixedRectangleTemplate(AlternatingRectangleTemplate):
    def __init__(
        self,
        width: int,
        height: int,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        super().__init__(
            Dimension(width, is_fixed=True),
            Dimension(height, is_fixed=True),
            default_x_increment,
            default_y_increment,
        )
