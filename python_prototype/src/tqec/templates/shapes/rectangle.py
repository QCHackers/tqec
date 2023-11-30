from tqec.templates.shapes.base import Shape
import typing as ty

import numpy


class Rectangle(Shape):
    def __init__(self, width: int, height: int) -> None:
        super().__init__()
        self._width = width
        self._height = height

    def instanciate(self, x_plaquette: int, z_plaquette: int, *_: int) -> numpy.ndarray:
        ret = numpy.zeros(self.shape, dtype=int)
        odd = slice(0, None, 2)
        even = slice(1, None, 2)
        ret[even, odd] = z_plaquette
        ret[odd, even] = z_plaquette
        ret[even, even] = x_plaquette
        ret[odd, odd] = x_plaquette
        return ret

    @property
    def shape(self) -> tuple[int, int]:
        return (self._height, self._width)

    def to_dict(self) -> dict[str, ty.Any]:
        return {
            "type": self.__class__.__name__,
            "kwargs": {
                "width": self._width,
                "height": self._height,
            },
        }

    def get_parameters(self) -> tuple[int, ...]:
        return (self._width, self._height)

    def set_parameters(self, parameters: tuple[int, ...]) -> None:
        assert len(parameters) == 2
        self._width, self._height = parameters


class RawRectangle(Rectangle):
    def __init__(self, indices: list[list[int]]) -> None:
        width: int
        height: int
        if len(indices) == 0:
            width, height = 0, 0
        else:
            width, height = len(indices[0]), len(indices)
        super().__init__(width, height)
        self._indices = indices

    def instanciate(self, *plaquette_indices: int) -> numpy.ndarray:
        try:
            return numpy.array(plaquette_indices)[self._indices]
        except IndexError as e:
            e.add_note(
                "RawRectangle instances should be constructed with 2-dimensional arrays "
                "that contain indices that will index the plaquette_indices provided to "
                "this method. The bigest index you provided at this instance creation is "
                f"{max(max(l) for l in self._indices)} "
                f"but you provided only {len(plaquette_indices)} plaquette indices "
                "when calling this method."
            )
            raise e

    def to_dict(self) -> dict[str, ty.Any]:
        return {"type": self.__class__.__name__, "kwargs": {"indices": self._indices}}
