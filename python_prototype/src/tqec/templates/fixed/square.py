from tqec.templates.fixed.base import FixedTemplate
from tqec.templates.shapes.square import AlternatingSquare

import typing as ty


class FixedSquare(FixedTemplate, AlternatingSquare):
    def __init__(self, dim: int) -> None:
        FixedTemplate.__init__(self)
        AlternatingSquare.__init__(self, dim)

    def to_dict(self) -> dict[str, ty.Any]:
        ret = FixedTemplate.to_dict(self)
        ret.update(AlternatingSquare.to_dict(self))
        return ret
