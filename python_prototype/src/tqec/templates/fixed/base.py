import typing as ty
from tqec.templates.base import Template


class FixedTemplate(Template):
    def __init__(self) -> None:
        Template.__init__(self)

    def scale_to(self, _: int) -> "FixedTemplate":
        # Do nothing
        return self

    def to_dict(self) -> dict[str, ty.Any]:
        return {"scalable": False}
