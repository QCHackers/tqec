import typing as ty
from dataclasses import dataclass

import numpy
from tqec.position import Shape2D
from tqec.templates.base import Template
from tqec.templates.scale import Dimension


@dataclass
class ScalableOffset:
    x: Dimension
    y: Dimension

    def scale_to(self, k: int) -> None:
        self.x.scale_to(k)
        self.y.scale_to(k)

    def to_dict(self) -> dict[str, ty.Any]:
        return {"x": self.x.to_dict(), "y": self.y.to_dict()}


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
        """Scales the scalable template and its offset to the given scale k.

        Note that this function scales to INLINE, so the instance on which it is called is
        modified in-place AND returned.

        :param k: the new scale of the component templates.
        :returns: self, once scaled.
        """
        self._shifted_template.scale_to(k)
        self._offset.scale_to(k)
        return self

    @property
    def shape(self) -> Shape2D:
        """Returns the current template shape.

        :returns: the numpy-like shape of the template.
        """
        tshape = self._shifted_template.shape
        return Shape2D(self._offset.x.value + tshape.x, self._offset.y.value + tshape.y)

    def to_dict(self) -> dict[str, ty.Any]:
        """Returns a dict-like representation of the instance.

        Used to implement to_json.
        """
        return super().to_dict() | {
            "shifted": {
                "template": self._shifted_template.to_dict(),
                "offset": self._offset.to_dict(),
            }
        }

    @property
    def expected_plaquettes_number(self) -> int:
        """Returns the number of plaquettes expected from the `instanciate` method.

        :returns: the number of plaquettes expected from the `instanciate` method.
        """
        return self._shifted_template.expected_plaquettes_number

    def instanciate(self, *plaquette_indices: int) -> numpy.ndarray:
        """Generate the numpy array representing the template.

        :param plaquette_indices: the plaquette indices that will be used to create the
            resulting array.
        :returns: a numpy array with the given plaquette indices arranged according
            to the underlying shape of the template.
        """
        arr = numpy.zeros(self.shape.to_numpy_shape(), dtype=int)
        tshape = self._shifted_template.shape
        xoffset, yoffset = self._offset.x.value, self._offset.y.value
        tarr = self._shifted_template.instanciate(*plaquette_indices)
        arr[yoffset : yoffset + tshape.y, xoffset : xoffset + tshape.x] = tarr
        return arr
