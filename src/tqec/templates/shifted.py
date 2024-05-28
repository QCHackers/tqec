import typing as ty
from dataclasses import dataclass

import numpy

from tqec.enums import TemplateOrientation
from tqec.templates.base import Template
from tqec.templates.scale import ScalableOffset, ScalableShape2D


class ShiftedTemplate(Template):
    def __init__(
        self,
        template: Template,
        offset: ScalableOffset,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        super().__init__(default_x_increment, default_y_increment)
        self._shifted_template = template
        self._offset = offset

    def scale_to(self, k: int) -> "ShiftedTemplate":
        self._shifted_template.scale_to(k)
        self._offset.scale_to(k)
        return self

    @property
    def shape(self) -> ScalableShape2D:
        tshape = self._shifted_template.shape
        return ScalableShape2D(self._offset.x + tshape.x, self._offset.y + tshape.y)

    @property
    def expected_plaquettes_number(self) -> int:
        return self._shifted_template.expected_plaquettes_number

    def instantiate(self, plaquette_indices: ty.Sequence[int]) -> numpy.ndarray:
        # Do not explicitely check here, the check is forwarded to the
        # shifted Template instance.
        arr = numpy.zeros(self.shape.to_numpy_shape(), dtype=int)
        tshape = self._shifted_template.shape.instantiate()
        xoffset, yoffset = self._offset.x.value, self._offset.y.value
        tarr = self._shifted_template.instantiate(plaquette_indices)
        arr[yoffset : yoffset + tshape.y, xoffset : xoffset + tshape.x] = tarr
        return arr

    def get_midline_plaquettes(
        self, orientation: TemplateOrientation = TemplateOrientation.HORIZONTAL
    ) -> list[tuple[int, int]]:
        return [
            (row + self._offset.x.value, column + self._offset.y.value)
            for row, column in self._shifted_template.get_midline_plaquettes(
                orientation
            )
        ]
