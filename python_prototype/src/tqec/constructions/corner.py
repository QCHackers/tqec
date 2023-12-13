from tqec.templates.orchestrator import TemplateOrchestrator
from tqec.templates.base import TemplateWithIndices
from tqec.templates.scalable.rectangle import ScalableRectangle
from tqec.templates.scalable.square import (
    ScalableAlternatingCornerSquare,
    ScalableAlternatingSquare,
)
from tqec.templates.fixed.rectangle import FixedRectangle
from tqec.templates.fixed.base import FixedRaw
from tqec.enums import CornerPositionEnum, ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF

from tqec.templates.orchestrator import TemplateOrchestrator


class ScalableCorner(TemplateOrchestrator):
    def __init__(self, dim: int) -> None:
        _templates = [
            # 0
            TemplateWithIndices(ScalableRectangle(dim, 1), [0, 1]),
            TemplateWithIndices(ScalableRectangle(1, dim), [2, 0]),
            TemplateWithIndices(ScalableAlternatingSquare(dim), [3, 4]),
            TemplateWithIndices(ScalableRectangle(1, dim), [0, 5]),
            TemplateWithIndices(FixedRectangle(1, 2), [2, 0]),
            # 5
            TemplateWithIndices(ScalableRectangle(dim, 2), [3, 4]),
            TemplateWithIndices(FixedRaw([[0, 0], [1, 0]]), [0, 6]),
            TemplateWithIndices(ScalableRectangle(dim, 1), [7, 0]),
            TemplateWithIndices(ScalableRectangle(1, dim), [2, 0]),
            TemplateWithIndices(
                ScalableAlternatingCornerSquare(dim, CornerPositionEnum.LOWER_LEFT),
                [
                    3,
                    4,
                    8,
                    9,
                    11,
                ],
            ),
            # 10
            TemplateWithIndices(ScalableRectangle(2, dim), [9, 8]),
            TemplateWithIndices(ScalableAlternatingSquare(dim), [9, 8]),
            TemplateWithIndices(ScalableRectangle(1, dim), [10, 0]),
            TemplateWithIndices(ScalableRectangle(dim, 1), [0, 12]),
            TemplateWithIndices(FixedRectangle(2, 1), [0, 12]),
            # 15
            TemplateWithIndices(ScalableRectangle(dim, 1), [0, 12]),
        ]
        _relations = [
            (0, ABOVE_OF, 2),
            (1, LEFT_OF, 2),
            (3, RIGHT_OF, 2),
            (4, BELOW_OF, 1),
            (5, BELOW_OF, 2),
            # For the moment, 6 is encoded as a FixedRectangle of size 2
            # as follow:
            #   0
            #   X
            # where X is the provided plaquette number.
            (6, RIGHT_OF, 5),
            (9, BELOW_OF, 5),
            (8, LEFT_OF, 9),
            (13, BELOW_OF, 9),
            (10, RIGHT_OF, 9),
            (11, RIGHT_OF, 10),
            (7, ABOVE_OF, 11),
            (12, RIGHT_OF, 11),
            (15, BELOW_OF, 11),
            (14, LEFT_OF, 15),
        ]
        TemplateOrchestrator.__init__(self, _templates)
        for source, relpos, target in _relations:
            self.add_relation(source, relpos, target)
