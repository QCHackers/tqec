import typing as ty
from abc import ABC, abstractmethod

import numpy
from tqec.position import Shape2D


class WrongNumberOfParametersException(Exception):
    def __init__(self, expected: int, provided: int) -> None:
        super().__init__(
            f"{provided} parameters were provided, but {expected} were expected."
        )


class BaseShape(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def instanciate(self, *_: int) -> numpy.ndarray:
        pass

    @property
    @abstractmethod
    def shape(self) -> Shape2D:
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, ty.Any]:
        pass

    @abstractmethod
    def get_parameters(self) -> tuple[int, ...]:
        pass

    @abstractmethod
    def set_parameters(self, parameters: tuple[int, ...]) -> None:
        pass
