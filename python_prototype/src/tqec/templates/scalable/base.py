from tqec.templates.base import Template
import typing as ty


class ScalableTemplate(Template):
    def __init__(self) -> None:
        Template.__init__(self)

    def to_dict(self) -> dict[str, ty.Any]:
        return {"scalable": True}
