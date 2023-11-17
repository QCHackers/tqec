from tqec.templates.base import Template


class FixedTemplate(Template):
    def __init__(self) -> None:
        Template.__init__(self)

    def scale_to(self, _: int) -> "FixedTemplate":
        # Do nothing
        return self
