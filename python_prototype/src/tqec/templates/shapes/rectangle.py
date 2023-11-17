from tqec.templates.base import Template

import numpy


class Rectangle(Template):
    def __init__(self, width: int, height: int) -> None:
        super().__init__()
        assert width != height, "Both width and height are equal, use a square."
        self._width = width
        self._height = height

    def instanciate(self, x_plaquette: int, z_plaquette: int, *_: int) -> numpy.ndarray:
        ret = numpy.zeros(self.shape, dtype=int)
        odd = slice(0, None, 2)
        even = slice(1, None, 2)
        ret[even, odd] = z_plaquette
        ret[odd, even] = z_plaquette
        ret[even, even] = x_plaquette
        ret[odd, odd] = x_plaquette
        return ret

    @property
    def shape(self) -> tuple[int, int]:
        return (self._height, self._width)

    def scale_to(self, k: int) -> Template:
        if self._width > self._height:
            self._width = k
        else:
            self._height = k
        return self
