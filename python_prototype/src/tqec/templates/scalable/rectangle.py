from tqec.templates.scalable.base import ScalableTemplate
from tqec.templates.shapes.rectangle import Rectangle


class ScalableRectangle(ScalableTemplate, Rectangle):
    def __init__(self, width: int, height: int) -> None:
        ScalableTemplate.__init__(self)
        Rectangle.__init__(self, width, height)
