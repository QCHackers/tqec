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
        _templates = [
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
            (14, RIGHT_OF, 15),
        ]
        TemplateOrchestrator.__init__(self, _templates)
        for source, relpos, target in _relations:
            self.add_relation(source, relpos, target)
