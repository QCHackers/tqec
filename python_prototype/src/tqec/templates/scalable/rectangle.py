from tqec.templates.base import Template
from tqec.templates.scalable.base import ScalableTemplate
from tqec.templates.shapes.rectangle import Rectangle
import typing as ty


class ScalableRectangle(ScalableTemplate, Rectangle):
    def __init__(
        self, width: int, height: int, scale_func: ty.Callable[[int], int] = lambda x: x
    ) -> None:
        ScalableTemplate.__init__(self, scale_func)
        Rectangle.__init__(self, width, height)

    def to_dict(self) -> dict[str, ty.Any]:
        ret = ScalableTemplate.to_dict(self)
        ret.update(Rectangle.to_dict(self))
        return ret

    def scale_to(self, k: int) -> Template:
        return Rectangle.scale_to(self, ScalableTemplate.get_scaled_scale(self, k))
