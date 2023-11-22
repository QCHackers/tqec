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
        """Create an instance of FixedRaw.

        :param plaquette_template: a 2-dimensional array of indices starting from 0.
            The indices in this array will be used to **index** the plaquette_indices
            list provided to the instantiate method.
        """
        FixedTemplate.__init__(self)
        self._plaquette_template = plaquette_template

    def to_dict(self) -> dict[str, ty.Any]:
        ret = FixedTemplate.to_dict(self)
        ret.update({"plaquette_template": self._plaquette_template})
        return ret

    def instanciate(self, *plaquette_indices: int) -> numpy.ndarray:
        try:
            return numpy.array(plaquette_indices)[self._plaquette_template]
        except IndexError as e:
            e.add_note(
                "FixedRaw instances should be constructed with 2-dimensional arrays "
                "that contain **indices** that will index the plaquette_indices provided to "
                "this method. The bigest index you provided at this instance creation is "
                f"{max(max(l) for l in self._plaquette_template)} "
                f"but you provided only {len(plaquette_indices)} plaquette indices "
                "when calling this method."
            )
            raise e

    @property
    def shape(self) -> tuple[int, int]:
        if len(self._plaquette_template) == 0:
            return (0, 0)
        return (len(self._plaquette_template), len(self._plaquette_template[0]))
