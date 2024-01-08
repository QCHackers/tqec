from tqec.templates.fixed.base import FixedTemplate
from tqec.templates.shapes.rectangle import Rectangle


class FixedRectangle(FixedTemplate):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(Rectangle(width, height))
