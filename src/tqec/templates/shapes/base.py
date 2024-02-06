import typing as ty
from abc import ABC, abstractmethod

import numpy
from tqec.exceptions import TQECException
from tqec.position import Shape2D


class WrongNumberOfParametersException(TQECException):
    def __init__(self, expected: int, provided: int) -> None:
        super().__init__(
            f"{provided} parameters were provided, but {expected} were expected."
        )


class BaseShape(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def instantiate(self, *_: int) -> numpy.ndarray:
        pass

    @property
    @abstractmethod
    def shape(self) -> Shape2D:
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, ty.Any]:
        pass

    @property
    @abstractmethod
    def expected_plaquettes_number(self) -> int:
        """Returns the number of plaquettes expected from the `instanciate` method.

        :returns: the number of plaquettes expected from the `instanciate` method.
        """
        pass

    @abstractmethod
    def get_parameters(self) -> tuple[int, ...]:
        pass

    @abstractmethod
    def set_parameters(self, parameters: tuple[int, ...]) -> None:
        pass
