import typing as ty
import numpy
from tqec.templates.base import Template


class FixedTemplate(Template):
    def __init__(self) -> None:
        Template.__init__(self)

    def scale_to(self, _: int) -> "FixedTemplate":
        # Do nothing
        return self

    def to_dict(self) -> dict[str, ty.Any]:
        return {"scalable": False}


class FixedRaw(FixedTemplate):
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
