from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import typing as ty

import numpy
from tqec.enums import CornerPositionEnum, TemplateRelativePositionEnum


def json_encoding_default(obj) -> str | dict | None:
    if isinstance(obj, CornerPositionEnum):
        return f"{obj.name}"
    elif isinstance(obj, TemplateRelativePositionEnum):
        return f"{obj.name}"
    raise TypeError(f"Type {type(obj).__name__} is not encodable in JSON")


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

    @abstractmethod
    def to_dict(self) -> dict[str, ty.Any]:
        pass

    def to_json(self, **kwargs) -> str:
        assert "default" not in kwargs, "No default allowed!"
        return json.dumps(self.to_dict(), default=json_encoding_default, **kwargs)


@dataclass
class TemplateWithPlaquettes:
    template: Template
    plaquettes: list[int]
