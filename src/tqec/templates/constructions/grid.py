from tqec.enums import BELOW_OF, RIGHT_OF
from tqec.templates.base import Template, TemplateWithIndices
from tqec.templates.composed import ComposedTemplate


class TemplateGrid(ComposedTemplate):
    def __init__(self, rows: int, cols: int, template: Template) -> None:
        plaquettes_indices_per_qubit = template.expected_plaquettes_number

        super().__init__([])

        template_indices: list[list[int]] = []
        for i in range(rows):
            template_indices.append([])
            for j in range(cols):
                twi = TemplateWithIndices(
                    template,
                    list(
                        range(
                            1 + (i * cols + j) * plaquettes_indices_per_qubit,
                            1 + (i * cols + j + 1) * plaquettes_indices_per_qubit,
                        )
                    ),
                )
                template_indices[i].append(self.add_template(twi))

        # First column
        for i in range(1, rows):
            self.add_relation(
                template_indices[i][0], BELOW_OF, template_indices[i - 1][0]
            )
        # Other templates
        for i in range(rows):
            for j in range(1, cols):
                self.add_relation(
                    template_indices[i][j], RIGHT_OF, template_indices[i][j - 1]
                )
