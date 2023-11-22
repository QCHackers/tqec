from tqec.templates.base import Template
import typing as ty


class ScalableTemplate(Template):
    def __init__(self, scale_func: ty.Callable[[int], int] = lambda x: x) -> None:
        Template.__init__(self)
        self._scale_func = scale_func

    def to_dict(self) -> dict[str, ty.Any]:
        return {"scalable": True}

    def get_scaled_scale(self, k: int) -> int:
        return self._scale_func(k)
