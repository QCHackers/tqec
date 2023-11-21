from tqec.templates.orchestrator import TemplateOrchestrator
from tqec.templates.base import TemplateWithPlaquettes
from tqec.templates.scalable.rectangle import ScalableRectangle
from tqec.templates.scalable.square import (
    ScalableAlternatingCornerSquare,
    ScalableAlternatingSquare,
)
from tqec.templates.fixed.rectangle import FixedRectangle
from tqec.enums import CornerPositionEnum, ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF

from tqec.templates.orchestrator import TemplateOrchestrator


class ScalableCorner(TemplateOrchestrator):
    def __init__(self, dim: int) -> None:
        self._template_instances = [
            # 0-th entry to nothing to adhere to the numbering on the slide.
            None,
            TemplateWithPlaquettes(ScalableRectangle(dim, 1), [0, 1]),
            TemplateWithPlaquettes(ScalableRectangle(1, dim), [2, 0]),
            TemplateWithPlaquettes(ScalableAlternatingSquare(dim), [2, 3]),
            TemplateWithPlaquettes(ScalableRectangle(1, dim), [0, 5]),
            TemplateWithPlaquettes(FixedRectangle(1, 2), [2, 0]),
            TemplateWithPlaquettes(ScalableRectangle(dim, 2), [3, 2]),
            TemplateWithPlaquettes(FixedRectangle(1, 2), [0, 6]),
            TemplateWithPlaquettes(ScalableRectangle(dim, 1), [7, 0]),
            TemplateWithPlaquettes(ScalableRectangle(1, dim), [2, 0]),
            TemplateWithPlaquettes(
                ScalableAlternatingCornerSquare(dim, CornerPositionEnum.LOWER_LEFT),
                [
                    2,
                    3,
                    8,
                    9,
                    11,
                ],
            ),
            TemplateWithPlaquettes(ScalableRectangle(2, dim), [9, 8]),
            TemplateWithPlaquettes(ScalableAlternatingSquare(dim), [9, 8]),
            TemplateWithPlaquettes(ScalableRectangle(1, dim), [10, 0]),
            TemplateWithPlaquettes(ScalableRectangle(dim, 1), [0, 12]),
            TemplateWithPlaquettes(FixedRectangle(2, 1), [0, 12]),
            TemplateWithPlaquettes(ScalableRectangle(dim, 1), [0, 12]),
        ]
        TemplateOrchestrator.__init__(self, self._template_instances[1])
        self._construct()

    def _construct(self) -> None:
        self.add_template(self.ti(3), BELOW_OF, self.ti(1)).add_template(
            self.ti(2), LEFT_OF, self.ti(3)
        ).add_template(self.ti(4), RIGHT_OF, self.ti(3)).add_template(
            self.ti(5), BELOW_OF, self.ti(2)
        ).add_template(
            self.ti(6), BELOW_OF, self.ti(3)
        ).and_also(
            RIGHT_OF, self.ti(5)
        ).add_template(
            self.ti(7), RIGHT_OF, self.ti(6)
        ).and_also(
            BELOW_OF, self.ti(4)
        ).add_template(
            self.ti(10), BELOW_OF, self.ti(6)
        ).add_template(
            self.ti(9), BELOW_OF, self.ti(5)
        ).and_also(
            LEFT_OF, self.ti(10)
        ).add_template(
            self.ti(14), BELOW_OF, self.ti(10)
        ).add_template(
            self.ti(11), RIGHT_OF, self.ti(10)
        ).add_template(
            self.ti(15), RIGHT_OF, self.ti(14)
        ).and_also(
            BELOW_OF, self.ti(11)
        ).add_template(
            self.ti(12), RIGHT_OF, self.ti(11)
        ).add_template(
            self.ti(8), ABOVE_OF, self.ti(12)
        ).add_template(
            self.ti(16), BELOW_OF, self.ti(12)
        ).and_also(
            RIGHT_OF, self.ti(15)
        ).add_template(
            self.ti(13), RIGHT_OF, self.ti(12)
        )

    def ti(self, index: int) -> TemplateWithPlaquettes:
        return self._template_instances[index]
