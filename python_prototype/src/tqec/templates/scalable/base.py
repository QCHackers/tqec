from tqec.templates.base import Template

from tqec.templates.shapes.base import Shape


class ScalableTemplate(Template):
    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
