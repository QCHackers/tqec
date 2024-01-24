from tqec.templates.base import Template
from tqec.templates.shapes.base import BaseShape


class DimensionNotEven(Exception):
    def __init__(self, *provided_dimensions: int) -> None:
        super().__init__(
            f"The provided dimension(s) {provided_dimensions} is(are) "
            "not even. Dimension must be even to be scalable!"
        )


class ScalableTemplate(Template):
    def __init__(self, shape: BaseShape) -> None:
        super().__init__(shape)
