from tqec.templates.base import AtomicTemplate
from tqec.templates.shapes.base import BaseShape


class ScalableTemplate(AtomicTemplate):
    def __init__(self, shape: BaseShape) -> None:
        super().__init__(shape)
