from tqec.templates.fixed.base import FixedTemplate
from tqec.templates.shapes.rectangle import Rectangle
import typing as ty


class FixedRectangle(FixedTemplate, Rectangle):
    def __init__(self, width: int, height: int) -> None:
        FixedTemplate.__init__(self)
        Rectangle.__init__(self, width, height)

    def to_dict(self) -> dict[str, ty.Any]:
        ret = FixedTemplate.to_dict(self)
        ret.update(Rectangle.to_dict(self))
        return ret
