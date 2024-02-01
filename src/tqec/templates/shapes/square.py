import typing as ty

import numpy
from tqec.enums import CornerPositionEnum
from tqec.templates.shapes.base import WrongNumberOfParametersException
from tqec.templates.shapes.rectangle import Rectangle


class AlternatingSquare(Rectangle):
    def __init__(self, dimension: int) -> None:
        super().__init__(dimension, dimension)

    def get_parameters(self) -> tuple[int, ...]:
        dimension, _ = super().get_parameters()
        return (dimension,)

    def set_parameters(self, parameters: tuple[int, ...]) -> None:
        if len(parameters) != 1:
            raise WrongNumberOfParametersException(1, len(parameters))
        dimension: int = parameters[0]
        super().set_parameters((dimension, dimension))

    def to_dict(self) -> dict[str, ty.Any]:
        return {
            "type": self.__class__.__name__,
            "kwargs": {"dimension": self.get_parameters()[0]},
        }


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
        ret = numpy.zeros(self.shape.to_numpy_shape(), dtype=int)
        # Fill ret as if it was in the upper-left corner and then correct
        ret[0, 0] = corner_plaquette
        dimension = super().get_parameters()[0]
        for i in range(dimension):
            for j in range(dimension):
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
