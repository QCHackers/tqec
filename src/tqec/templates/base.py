import json
import typing as ty
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy
from tqec.enums import CornerPositionEnum, TemplateRelativePositionEnum
from tqec.exceptions import TQECException
from tqec.position import Displacement, Shape2D
from tqec.templates.shapes.base import BaseShape


def _json_encoding_default(obj) -> str | dict | None:
    """Define additional defaults to transform instances to JSON.

    This function is given as parameter to json.dumps to provide a
    way to translate the enumerations used by some templates to JSON
    data.

    :raises TypeError: if an instance of a unimplemented type is
        provided as parameter.
    """
    if isinstance(obj, CornerPositionEnum):
        return f"{obj.name}"
    elif isinstance(obj, TemplateRelativePositionEnum):
        return f"{obj.name}"
    raise TypeError(f"Type {type(obj).__name__} is not encodable in JSON")


class JSONEncodable(ABC):
    @abstractmethod
    def to_dict(self) -> dict[str, ty.Any]:
        """Returns a dict-like representation of the instance.

        Used to implement to_json.
        """
        pass

    def to_json(self, **kwargs) -> str:
        """Returns a JSON representation of the instance.

        :param kwargs: keyword arguments forwarded to the json.dumps function. The "default"
            keyword argument should NOT be present.
        :returns: the JSON representation of the instance.
        :raises DefaultKeyInKwargs: if the "default" key is present in kwargs.
        """
        if "default" in kwargs:
            raise TQECException(
                f"The 'default' key has been found with value '{kwargs.get('default')}' in the provided kwargs."
                " 'default' key is prohibited in the public API as it is changed internally."
            )
        return json.dumps(self.to_dict(), default=_json_encoding_default, **kwargs)


class Template(JSONEncodable):
    def __init__(
        self,
        shape: BaseShape,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        """Base class for all the templates.

        This class is the base of all templates and provide the necessary interface
        that all templates should implement to be usable by the library.

        Each template should have a shape, represented by a Shape instance, and encoding
        how the template scales and its plaquettes.

        The default increments define the distance between two plaquettes.
        For example a default_x_increment of 2 means that two 2x2 plaquettes will share
        a common edge.

        :param shape: the underlying template shape.
        :param default_x_increment: default increment in the x direction between two plaquettes.
        :param default_y_increment: default increment in the y direction between two plaquettes.
        """
        super().__init__()
        self._shape_instance = shape
        self._default_increments = Displacement(
            default_x_increment, default_y_increment
        )

    def instantiate(self, *plaquette_indices: int) -> numpy.ndarray:
        """Generate the numpy array representing the template.

        :param plaquette_indices: the plaquette indices that will be forwarded to the
            underlying Shape instance's instantiate method.
        :returns: a numpy array with the given plaquette indices arranged according
            to the underlying shape of the template.
        """
        return self._shape_instance.instantiate(*plaquette_indices)

    @property
    def shape(self) -> Shape2D:
        """Returns the current template shape.

        This should not be confused with the underlying shape of the template. Here
        shape can mean:
        - the Shape instance that defines what the template will look like and,
        - the numpy-like shape, that is represented as 2 integers encoding the sizes
          of the returned numpy array in both dimensions.

        :returns: the numpy-like shape of the template.
        """
        return self._shape_instance.shape

    @abstractmethod
    def scale_to(self, k: int) -> "Template":
        """Scales self to the given scale k.

        The scale k of a **scalable template** is defined to be **half** the dimension/size
        of the **scalable axis** of the template. For example, a scalable 4x4 square T has a
        scale of 2 for both its axis. This means the dimension/size of the scaled axis is
        enforced to be even, which avoids some invalid configuration of the template.

        Note that this function scales to INLINE, so the instance on which it is called is
        modified in-place AND returned.

        :param k: the new scale of the template.
        :returns: self, once scaled.
        """
        pass

    def to_dict(self) -> dict[str, ty.Any]:
        """Returns a dict-like representation of the instance.

        Used to implement to_json.
        """
        # self.__class__ is the type of the instance this method is called on, taking into
        # account inheritance. So this is not always "Template" here, as a subclass of
        # Template could use this method and self.__class__ would be this subclass type.
        # This is intentional.
        return {
            "type": self.__class__.__name__,
            "shape": self.shape_instance.to_dict(),
            "default_increments": {
                "x": self._default_increments.x,
                "y": self._default_increments.y,
            },
        }

    @property
    def shape_instance(self) -> BaseShape:
        """Get the underlying shape instance.

        Not to be confused with the shape property, this property recovers the BaseShape
        instance that is stored by the Template instance it is called on. It does NOT return
        the numpy-like Shape2D instance representing the sizes of the templates.
        """
        return self._shape_instance

    def get_increments(self) -> Displacement:
        """Get the default increments of the template.

        :returns: a displacement of the default increments in the x and y directions.
        """
        return self._default_increments


@dataclass
class TemplateWithIndices:
    """A wrapper around a Template instance and the indices representing the plaquettes it should be instantiated with."""

    template: Template
    indices: list[int]
