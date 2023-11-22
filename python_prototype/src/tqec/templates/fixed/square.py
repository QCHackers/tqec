import typing as ty
import numpy
from tqec.templates.fixed.base import FixedTemplate
from tqec.templates.shapes.square import AlternatingSquare


class FixedAlternatingSquare(FixedTemplate, AlternatingSquare):
    def __init__(self, dim: int) -> None:
        FixedTemplate.__init__(self)
        AlternatingSquare.__init__(self, dim)

    def to_dict(self) -> dict[str, ty.Any]:
        ret = FixedTemplate.to_dict(self)
        ret.update(AlternatingSquare.to_dict(self))
        return ret


class FixedRawSquare(FixedTemplate):
    def __init__(self, plaquette_template: list[list[int]]) -> None:
        FixedTemplate.__init__(self)
        self._plaquette_template = plaquette_template

    def to_dict(self) -> dict[str, ty.Any]:
        ret = FixedTemplate.to_dict(self)
        ret.update({"plaquette_template": self._plaquette_template})
        return ret

    def instanciate(self, *plaquette_indices: int) -> numpy.ndarray:
        return numpy.array(plaquette_indices)[self._plaquette_template]

    @property
    def shape(self) -> tuple[int, int]:
        if len(self._plaquette_template) == 0:
            return (0, 0)
        return (len(self._plaquette_template), len(self._plaquette_template[0]))
