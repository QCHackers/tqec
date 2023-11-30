from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import typing as ty

import numpy
from tqec.enums import CornerPositionEnum, TemplateRelativePositionEnum
from tqec.templates.shapes.base import Shape


def json_encoding_default(obj) -> str | dict | None:
    if isinstance(obj, CornerPositionEnum):
        return f"{obj.name}"
    elif isinstance(obj, TemplateRelativePositionEnum):
        return f"{obj.name}"
    raise TypeError(f"Type {type(obj).__name__} is not encodable in JSON")


class Template(ABC):
    def __init__(self, shape: Shape) -> None:
        super().__init__()
        self._shape_instance = shape

    def instanciate(self, *plaquette_indices: int) -> numpy.ndarray:
        return self._shape_instance.instanciate(*plaquette_indices)

    @property
    def shape(self) -> tuple[int, int]:
        return self._shape_instance.shape

    @abstractmethod
    def scale_to(self, k: int) -> "Template":
        pass

    def to_dict(self) -> dict[str, ty.Any]:
        # self.__class__ is the type of the instance this method is called on, taking into
        # account inheritance. So this is not always "Template" here, as a subclass of 
        # Template could use this method and self.__class__ would be this subclass type.
        # This is intentional.
        return {"type": self.__class__.__name__, "shape": self.shape_instance.to_dict()}

    def to_json(self, **kwargs) -> str:
        assert "default" not in kwargs, "No default allowed!"
        return json.dumps(self.to_dict(), default=json_encoding_default, **kwargs)

    @property
    def shape_instance(self) -> Shape:
        return self._shape_instance


@dataclass
class TemplateWithPlaquettes:
    template: Template
    plaquettes: list[int]
