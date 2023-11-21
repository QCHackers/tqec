from tqec.templates.base import Template
from tqec.enums import CornerPositionEnum

import typing as ty

import numpy


class AlternatingSquare(Template):
    def __init__(self, dimension: int) -> None:
        super().__init__()
        self._dimension = dimension

    def instanciate(self, x_plaquette: int, z_plaquette: int, *_: int) -> numpy.ndarray:
        ret = numpy.zeros(self.shape, dtype=int)
        odd = slice(0, None, 2)
        even = slice(1, None, 2)
        ret[even, odd] = x_plaquette
        ret[odd, even] = x_plaquette
        ret[even, even] = z_plaquette
        ret[odd, odd] = z_plaquette
        return ret

    @property
    def shape(self) -> tuple[int, int]:
        return (self._dimension, self._dimension)

    def scale_to(self, k: int) -> Template:
        self._dimension = k
        return self

    def to_dict(self) -> dict[str, ty.Any]:
        return {"type": "square", "dimension": self._dimension}


class AlternatingCornerSquare(AlternatingSquare):
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

    def __init__(self, dimension: int, corner_position: CornerPositionEnum) -> None:
        super().__init__(dimension)
        self._corner_position = corner_position

    def instanciate(
        self,
        x_plaquette: int,
        z_plaquette: int,
        x_plaquette_flipped: int,
        z_plaquette_flipped: int,
        corner_plaquette: int,
        *_: int,
    ) -> numpy.ndarray:
        ret = numpy.zeros(self.shape, dtype=int)
        # Fill ret as if it was in the upper-left corner and then correct
        ret[0, 0] = corner_plaquette
        for i in range(self._dimension):
            for j in range(self._dimension):
                if i == j == 0:
                    ret[i, j] = corner_plaquette
                elif i > j:
                    if (i + j) % 2 == 1:
                        ret[i, j] = z_plaquette
                    else:
                        ret[i, j] = x_plaquette
                else:
                    if (i + j) % 2 == 1:
                        ret[i, j] = z_plaquette_flipped
                    else:
                        ret[i, j] = x_plaquette_flipped
        # Correct ret and return
        return self._TRANSFORMATIONS[self._corner_position](ret)

    def to_dict(self) -> dict[str, ty.Any]:
        ret = super().to_dict()
        ret.update({"corner": self._corner_position})
        return ret
