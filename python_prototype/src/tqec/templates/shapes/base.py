from abc import ABC, abstractmethod
import typing as ty

import numpy


class Shape(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def instanciate(self, *_: int) -> numpy.ndarray:
        pass

    @property
    @abstractmethod
    def shape(self) -> tuple[int, int]:
        pass

    # @abstractmethod
    # def to_dict(self) -> dict[str, ty.Any]:
    #     pass

    @abstractmethod
    def get_parameters(self) -> tuple[int, ...]:
        pass

    @abstractmethod
    def set_parameters(self, parameters: tuple[int, ...]) -> None:
        pass
