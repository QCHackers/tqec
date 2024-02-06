from tqec.templates.base import AtomicTemplate
from tqec.templates.shapes.base import BaseShape
from tqec.templates.shapes.rectangle import RawRectangle


class FixedTemplate(AtomicTemplate):
    def __init__(self, shape: BaseShape) -> None:
        super().__init__(shape)

    def scale_to(self, _: int) -> "FixedTemplate":
        # Do nothing
        return self


class FixedRaw(FixedTemplate):
    def __init__(self, plaquette_template: list[list[int]]) -> None:
        """Create an instance of FixedRaw.

        :param plaquette_template: a 2-dimensional array of indices starting from 0.
            The indices in this array will be used to **index** the plaquette_indices
            list provided to the instantiate method.
        """
        super().__init__(RawRectangle(plaquette_template))
