from tqec.templates.scalable.base import ScalableTemplate
from tqec.templates.shapes.rectangle import Rectangle
import typing as ty


class ScalableRectangle(ScalableTemplate, Rectangle):
    def __init__(self, width: int, height: int) -> None:
        ScalableTemplate.__init__(self)
        Rectangle.__init__(self, width, height)

    def to_dict(self) -> dict[str, ty.Any]:
        ret = ScalableTemplate.to_dict(self)
        ret.update(Rectangle.to_dict(self))
        return ret
