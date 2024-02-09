from __future__ import annotations

import json
import typing as ty
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy
from tqec.enums import CornerPositionEnum, TemplateRelativePositionEnum
from tqec.exceptions import TQECException
from tqec.position import Displacement, Shape2D


def _json_encoding_default(obj) -> str | dict | None:
    """Define additional defaults to transform instances to JSON.

    This function is given as parameter to json.dumps to provide a
    way to translate the enumerations used by some templates to JSON
    data.

    Raises:
        TypeError: if an instance of a unimplemented type is provided as
            parameter.
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

        Args:
            **kwargs: keyword arguments forwarded to the json.dumps function.
                The "default" keyword argument should NOT be present.

        Returns:
            the JSON representation of the instance.

        Raises:
            TQECException: if the "default" key is present in kwargs.
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
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        """Base class for all the templates.

        This class is the base of all templates and provide the necessary interface
        that all templates should implement to be usable by the library.

        Args:
            default_x_increment: default increment in the x direction between
                two plaquettes.
            default_y_increment: default increment in the y direction between
                two plaquettes.
        """
        super().__init__()
        self._default_increments = Displacement(
            default_x_increment, default_y_increment
        )

    @abstractmethod
    def instantiate(self, *plaquette_indices: int) -> numpy.ndarray:
        """Generate the numpy array representing the template.

        Args:
            *plaquette_indices: the plaquette indices that will be forwarded to
                the underlying Shape instance's instantiate method.

        Returns:
            a numpy array with the given plaquette indices arranged according to
            the underlying shape of the template.
        """
        pass

    @abstractmethod
    def scale_to(self, k: int) -> "Template":
        """Scales self to the given scale k.

        Note that this function scales the template instance INLINE. Rephrasing, the
        instance on which this method is called is modified in-place AND returned.

        The input parameter ``k`` corresponds to an abstract scale that may be
        forwarded to
        1. various :class:`Dimension` instances,
        2. other :class:`Template` instances in the case of templates modifying
           existing instances,
        3. anything else that the subclass might implement.

        Args:
            k: the new scale of the template.

        Returns:
            self, once scaled.
        """
        pass

    @property
    @abstractmethod
    def shape(self) -> Shape2D:
        """Returns the current template shape.

        Returns:
            the shape of the template.
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
            "default_increments": {
                "x": self._default_increments.x,
                "y": self._default_increments.y,
            },
        }

    @property
    @abstractmethod
    def expected_plaquettes_number(self) -> int:
        """Returns the number of plaquettes expected from the `instantiate` method.

        Returns:
            the number of plaquettes expected from the `instantiate` method.
        """
        pass

    def get_increments(self) -> Displacement:
        """Get the default increments of the template.

        Returns:
            a displacement of the default increments in the x and y directions.
        """
        return self._default_increments


@dataclass
class TemplateWithIndices:
    """A wrapper around a Template instance and the indices representing the plaquettes
    it should be instantiated with."""

    template: Template
    indices: list[int]
