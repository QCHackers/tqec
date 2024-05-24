from __future__ import annotations

import typing as ty
from abc import abstractmethod
from dataclasses import dataclass

import numpy

from tqec.exceptions import TQECException
from tqec.position import Displacement, Shape2D
from tqec.templates.scale import ScalableShape2D
from tqec.templates.schemas import InstantiableTemplateModel


class Template:
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

    def _check_plaquette_number(
        self, plaquette_indices: ty.Sequence[int], expected_plaquettes_number: int
    ) -> None:
        """Checks the number of provided plaquettes.

        This method should be called to check that the number of plaquette indices
        provided to the ``instantiate`` method is correct.

        Note:
            Be warry when calling this method by providing ``self.expected_plaquettes_number``
            as it is the number of expected plaquettes for the type of the self instance,
            which might NOT be the same as the number of expected plaquette for the
            ``instantiate`` method this method is called in (e.g., if a Template subclass `C`
            is delegating at least part of its ``instantiate`` method to a parent class `P`,
            ``type(self)`` will always be `C` and ``self.expected_plaquettes_number`` will
            always be ``C.expected_plaquettes_number``, even if we are within ``S.instantiate``).

        Args:
            plaquette_indices: the indices provided to the ``instantiate`` method.
            expected_plaquettes_number: the number of plaquettes expected in
                ``plaquette_indices``.
        Raises:
            TQECError: when there is not enough plaquette indices to instantiate
                the ``Template`` instance.
        """
        if len(plaquette_indices) < expected_plaquettes_number:
            raise TQECException(
                f"Calling an instantiate method that requires "
                f"{expected_plaquettes_number} plaquettes, but only "
                f"{len(plaquette_indices)} were provided."
            )

    @abstractmethod
    def instantiate(self, plaquette_indices: ty.Sequence[int]) -> numpy.ndarray:
        """Generate the numpy array representing the template.

        Args:
            plaquette_indices: the plaquette indices that will be forwarded to
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

    @property
    @abstractmethod
    def scalable_shape(self) -> ScalableShape2D:
        """Returns the current template shape.

        Returns:
            the shape of the template.
        """
        pass

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

    @abstractmethod
    def to_model(self) -> InstantiableTemplateModel:
        pass


@dataclass
class TemplateWithIndices:
    """A wrapper around a Template instance and the indices representing the plaquettes
    it should be instantiated with."""

    template: Template
    indices: list[int]

    def __post_init__(self):
        if self.template.expected_plaquettes_number != len(self.indices):
            raise TQECException(
                f"Creating a {self.__class__.__name__} instance with the template "
                f"{self.template} (that requires {self.template.expected_plaquettes_number} "
                f"plaquette indices) and a non-matching number of plaquette indices "
                f"{self.indices}."
            )
        if any(i < 0 for i in self.indices):
            raise TQECException(
                "Cannot have negative plaquette indices. Found a negative index "
                f"in {self.indices}."
            )
