from tqec.enums import ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF, CornerPositionEnum
from tqec.templates.base import TemplateWithIndices
from tqec.templates.fixed.base import FixedRaw
from tqec.templates.fixed.rectangle import FixedRectangle
from tqec.templates.orchestrator import TemplateOrchestrator
from tqec.templates.scalable.rectangle import ScalableRectangle
from tqec.templates.scalable.square import (
    ScalableAlternatingCornerSquare,
    ScalableAlternatingSquare,
)


class ScalableCorner(TemplateOrchestrator):
    def __init__(self, dim: int) -> None:
        """A scalable corner template.

        This corner template can be used to move an error-corrected qubit to another
        location on the chip. This is the basic building block to perform error-corrected
        computations.

        The below text represents this template for an input `dim` of 4.

        ```text
        .  .  1  .  1  .  .  .  .  .  .  .
        2  3  4  3  4  .  .  .  .  .  .  .
        .  4  3  4  3  5  .  .  .  .  .  .
        2  3  4  3  4  .  .  .  .  .  .  .
        .  4  3  4  3  5  .  .  .  .  .  .
        2  3  4  3  4  .  .  .  .  .  .  .
        .  4  3  4  3  6  .  7  .  7  .  .
        2  4  3  4  8  9  8  9  8  9  8 10
        .  3  4  8  9  8  9  8  9  8  9  .
        2  4  8  9  8  9  8  9  8  9  8 10
        . 11  9  8  9  8  9  8  9  8  9  .
        .  . 12  . 12  . 12  . 12  . 12  .
        ```

        :param dim: dimension (code distance - 1) of the initial error-corrected qubit.
        """
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
            TemplateWithIndices(ScalableRectangle(2, dim, scale_width=False), [9, 8]),
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
            # For the moment, 6 is encoded as a FixedRaw of size 2x2
            # as follow:
            #   0 0
            #   X 0
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
