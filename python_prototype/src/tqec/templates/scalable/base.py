from tqec.templates.base import Template
import typing as ty

from tqec.templates.shapes.base import Shape


class ScalableTemplate(Template):
    def __init__(
        self, shape: Shape, scale_func: ty.Callable[[int], int] = lambda x: x
    ) -> None:
        super().__init__(shape)
        self._scale_func = scale_func

    def get_scaled_scale(self, k: int) -> int:
        return self._scale_func(k)
