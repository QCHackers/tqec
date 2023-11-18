from tqec.templates.fixed.base import FixedTemplate
from tqec.templates.shapes.square import AlternatingSquare


class FixedSquare(FixedTemplate, AlternatingSquare):
    def __init__(self, dim: int) -> None:
        FixedTemplate.__init__(self)
        AlternatingSquare.__init__(self, dim)
