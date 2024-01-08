from tqec.templates.fixed.base import FixedTemplate
from tqec.templates.shapes.square import AlternatingSquare


class FixedAlternatingSquare(FixedTemplate):
    def __init__(self, dim: int) -> None:
        super().__init__(AlternatingSquare(dim))
