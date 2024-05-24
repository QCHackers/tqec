from tqec.templates.atomic.rectangle import (
    AlternatingRectangleTemplate,
    RawRectangleTemplate,
)
from tqec.templates.atomic.square import AlternatingSquareTemplate
from tqec.templates.base import Template
from tqec.templates.scale import (
    Dimension,
    FixedDimension,
    LinearFunction,
)
from tqec.templates.schemas import InstantiableTemplateModel


class TemplateLibrary:
    def __init__(self) -> None:
        self._templates: list[Template] = []
        self._descriptions: list[InstantiableTemplateModel] = []

    def add_template(self, name: str, template: Template):
        indices = list(range(1, template.expected_plaquettes_number + 1))
        description = InstantiableTemplateModel(
            name=name,
            shape=template.scalable_shape,
            instantiation=template.instantiate(indices).tolist(),
        )
        self._templates.append(template)
        self._descriptions.append(description)

    def get_descriptions(self) -> list[InstantiableTemplateModel]:
        return self._descriptions


PREDEFINED_TEMPLATES_LIBRARY = TemplateLibrary()
PREDEFINED_TEMPLATES_LIBRARY.add_template("1x1", RawRectangleTemplate([[0]]))
PREDEFINED_TEMPLATES_LIBRARY.add_template(
    "2kx1",
    AlternatingRectangleTemplate(FixedDimension(1), Dimension(1, LinearFunction(2, 0))),
)
PREDEFINED_TEMPLATES_LIBRARY.add_template(
    "1x2k",
    AlternatingRectangleTemplate(
        Dimension(1, LinearFunction(2, 0)),
        FixedDimension(1),
    ),
)
PREDEFINED_TEMPLATES_LIBRARY.add_template(
    "2kx2k",
    AlternatingSquareTemplate(Dimension(1, LinearFunction(2, 0))),
)
