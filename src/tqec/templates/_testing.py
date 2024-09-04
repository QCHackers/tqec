from typing import Sequence

import numpy
import numpy.typing as npt
from typing_extensions import override

from tqec.exceptions import TQECException
from tqec.position import Displacement, Shape2D
from tqec.templates.base import Template
from tqec.templates.enums import TemplateSide
from tqec.templates.scale import LinearFunction, PiecewiseLinearFunction, Scalable2D


class FixedTemplate(Template):
    """A fixed template, only used internally for testing."""

    def __init__(
        self,
        indices: Sequence[Sequence[int]],
        k: int = 2,
        default_increments: Displacement | None = None,
    ) -> None:
        super().__init__(k, default_increments)
        self._indices: npt.NDArray[numpy.int_] = numpy.array(
            [list(line) for line in indices]
        )

    @override
    def instantiate(
        self, plaquette_indices: Sequence[int] | None = None
    ) -> npt.NDArray[numpy.int_]:
        if plaquette_indices is None:
            plaquette_indices = list(range(1, self.expected_plaquettes_number + 1))

        return numpy.array(plaquette_indices)[self._indices]

    @property
    @override
    def scalable_shape(self) -> Scalable2D:
        y, x = self._indices.shape
        return Scalable2D(
            PiecewiseLinearFunction.from_linear_function(LinearFunction(0, x)),
            PiecewiseLinearFunction.from_linear_function(LinearFunction(0, y)),
        )

    @property
    @override
    def expected_plaquettes_number(self) -> int:
        return max((max(line, default=0) for line in self._indices), default=0) + 1

    @override
    def get_plaquette_indices_on_sides(self, sides: list[TemplateSide]) -> list[int]:
        raise NotImplementedError(
            "Cannot call FixedTemplate.get_plaquette_indices_on_sides."
        )
