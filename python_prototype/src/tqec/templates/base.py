from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy


class Template(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def instanciate(self, *plaquette_indices: int) -> numpy.ndarray:
        pass

    @abstractmethod
    def scale_to(self, k: int) -> "Template":
        pass

    @property
    @abstractmethod
    def shape(self) -> tuple[int, int]:
        pass


@dataclass
class TemplateWithPlaquettes:
    template: Template
    plaquettes: list[int]
