from abc import ABC, abstractmethod
from typing import Sequence

import numpy
import numpy.typing as npt
from typing_extensions import override

from tqec.exceptions import TQECException
from tqec.position import Displacement, Shape2D
from tqec.templates.enums import TemplateOrientation, TemplateSide
from tqec.templates.scale import Scalable2D, round_or_fail


class Template(ABC):
    def __init__(
        self, k: int = 2, default_increments: Displacement | None = None
    ) -> None:
        """Base class for all the templates.

        This class is the base of all templates and provide the necessary interface
        that all templates should implement to be usable by the library.

        Args:
            k: initial value for the scaling parameter.
            default_increments: default increments between two plaquettes. Defaults
                to `Displacement(2, 2)` when `None`
        """
        super().__init__()
        self._k = k
        self._default_increments = default_increments or Displacement(2, 2)

    @abstractmethod
    def instantiate(
        self, plaquette_indices: Sequence[int] | None = None
    ) -> npt.NDArray[numpy.int_]:
        """Generate the numpy array representing the template.

        Args:
            plaquette_indices: the plaquette indices that will be forwarded to
                the underlying Shape instance's instantiate method. Defaults
                to `range(1, self.expected_plaquettes_number + 1)` if `None`.

        Returns:
            a numpy array with the given plaquette indices arranged according to
            the underlying shape of the template.
        """

    def scale_to(self, k: int) -> None:
        """Scales self to the given scale k.

        Note that this function scales the template instance INLINE.

        Args:
            k: the new scale of the template.
        """
        self._k = k

    @property
    def k(self) -> int:
        return self._k

    @property
    def shape(self) -> Shape2D:
        """Returns the current template shape."""
        sshape = self.scalable_shape
        return Shape2D(
            round_or_fail(sshape.x(self._k)), round_or_fail(sshape.y(self._k))
        )

    @property
    @abstractmethod
    def scalable_shape(self) -> Scalable2D:
        """Returns a scalable version of the template shape."""

    @abstractmethod
    def get_midline_plaquettes(
        self, orientation: TemplateOrientation = TemplateOrientation.HORIZONTAL
    ) -> list[tuple[int, int]]:
        """Returns the default observable qubits for the template.

        If the template has a simple shape, this returns the plaquettes on the ``midline''
        of the template.
        By convention, it returns the plaquettes above the midline for the horizontal case
        and to the left of the midline for the vertical case.

        Args:
            orientation: Horizontal or vertical qubits. Defaults to horizontal.

        Returns:
            The sequence of qubits and offsets.

        Raises:
            TQECException: If the midline is not uniquely defined.
        """

    @property
    @abstractmethod
    def expected_plaquettes_number(self) -> int:
        """Returns the number of plaquettes expected from the `instantiate`
        method.

        Returns:
            the number of plaquettes expected from the `instantiate` method.
        """

    def get_increments(self) -> Displacement:
        """Get the default increments of the template.

        Returns:
            a displacement of the default increments in the x and y directions.
        """
        return self._default_increments

    @abstractmethod
    def get_plaquette_indices_on_sides(self, sides: list[TemplateSide]) -> list[int]:
        """Get the indices of plaquettes that are located on the provided
        sides.

        Args:
            sides: the sides to recover plaquettes from.

        Returns:
            a non-ordered list of plaquette numbers.
        """


class SquareTemplate(Template):
    @override
    def get_midline_plaquettes(
        self, orientation: TemplateOrientation = TemplateOrientation.HORIZONTAL
    ) -> list[tuple[int, int]]:
        midline_shape, iteration_shape = self.shape.x, self.shape.y
        if midline_shape % 2 == 1:
            raise TQECException(
                "Midline is not defined for odd "
                + f"{'height' if orientation == TemplateOrientation.HORIZONTAL else 'width'}."
            )
        midline = midline_shape // 2 - 1
        if orientation == TemplateOrientation.VERTICAL:
            return [(row, midline) for row in range(iteration_shape)]
        return [(midline, column) for column in range(iteration_shape)]
