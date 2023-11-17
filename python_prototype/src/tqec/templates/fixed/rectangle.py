from tqec.templates.fixed.base import FixedTemplate
from tqec.templates.shapes.rectangle import Rectangle


class FixedRectangle(FixedTemplate, Rectangle):
    def __init__(self, width: int, height: int) -> None:
        FixedTemplate.__init__(self)
        Rectangle.__init__(self, width, height)
