from tqec.templates.atomic.rectangle import (
    AlternatingRectangleTemplate,
    RawRectangleTemplate,
)
from tqec.templates.atomic.square import AlternatingSquareTemplate
from tqec.templates.base import Template
from tqec.templates.scale import LinearFunction
from tqec.templates.schemas import (
    InstantiableTemplateDescriptionModel,
    TemplateLibraryModel,
)


class TemplateLibrary:
    def __init__(self) -> None:
        self._templates: dict[str, Template] = dict()

    def add_template(self, name: str, template: Template):
        self._templates[name] = template

    def to_model(self) -> TemplateLibraryModel:
        return TemplateLibraryModel(
            templates=[
                InstantiableTemplateDescriptionModel(
                    name=name,
                    shape=template.scalable_shape,
                    instantiation=template.instantiate(
                        list(range(1, template.expected_plaquettes_number + 1))
                    ).tolist(),
                    expected_plaquettes_number=template.expected_plaquettes_number,
                )
                for name, template in self._templates.items()
            ]
        )


PREDEFINED_TEMPLATES_LIBRARY = TemplateLibrary()
PREDEFINED_TEMPLATES_LIBRARY.add_template("1x1", RawRectangleTemplate([[0]]))
PREDEFINED_TEMPLATES_LIBRARY.add_template(
    "2kx1",
    AlternatingRectangleTemplate(LinearFunction(0, 1), LinearFunction(2, 0)),
)
PREDEFINED_TEMPLATES_LIBRARY.add_template(
    "1x2k",
    AlternatingRectangleTemplate(
        LinearFunction(2, 0),
        LinearFunction(0, 1),
    ),
)
PREDEFINED_TEMPLATES_LIBRARY.add_template(
    "2kx2k",
    AlternatingSquareTemplate(LinearFunction(2, 0)),
)
