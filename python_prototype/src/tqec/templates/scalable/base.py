from tqec.templates.base import Template

from tqec.templates.shapes.base import BaseShape


class ScalableTemplate(Template):
    def __init__(self, shape: BaseShape) -> None:
        super().__init__(shape)
