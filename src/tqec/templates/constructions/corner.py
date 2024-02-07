from tqec.enums import ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF, CornerPositionEnum
from tqec.templates.base import TemplateWithIndices
from tqec.templates.composed import ComposedTemplate
from tqec.templates.fixed.base import FixedRaw
from tqec.templates.scalable.rectangle import ScalableRectangle
from tqec.templates.scalable.square import (
    ScalableAlternatingCornerSquare,
    ScalableAlternatingSquare,
)


class ScalableCorner(ComposedTemplate):
    def __init__(self, k: int) -> None:
        """A scalable corner template.

        This corner template can be used to move an error-corrected qubit to another
        location on the chip. This is the basic building block to perform error-corrected
        computations.

        The scale k of a **scalable template** is defined to be **half** the dimension/size
        of the **scalable axis** of the template. For example, a scalable 4x4 square has a
        scale of 2 for both its axis. This means the dimension/size of the scaled axis is
        enforced to be even, which avoids some invalid configuration of the template.

        The below text represents this template for an input `k` of 2.

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

        Args:
            k: scale of the initial error-corrected qubit.
        """
        dim = 2 * k
        _templates = [
            # 0
            TemplateWithIndices(ScalableRectangle(dim, 1), [0, 1]),
            TemplateWithIndices(ScalableRectangle(1, dim), [2, 0]),
            TemplateWithIndices(ScalableAlternatingSquare(dim), [3, 4]),
            TemplateWithIndices(ScalableRectangle(1, dim), [0, 5]),
            TemplateWithIndices(FixedRaw([[0]]), [2]),
            # 5
            TemplateWithIndices(ScalableRectangle(dim, 2), [3, 4]),
            TemplateWithIndices(FixedRaw([[0]]), [6]),
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
            TemplateWithIndices(FixedRaw([[0]]), [12]),
            # 15
            TemplateWithIndices(ScalableRectangle(dim, 1), [0, 12]),
        ]
        relative_positions = [
            (0, ABOVE_OF, 2),
            (1, LEFT_OF, 2),
            (3, RIGHT_OF, 2),
            (5, BELOW_OF, 2),
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
        pinned_corners = [
            ((6, CornerPositionEnum.LOWER_LEFT), (9, CornerPositionEnum.UPPER_RIGHT)),
            ((4, CornerPositionEnum.UPPER_RIGHT), (2, CornerPositionEnum.LOWER_LEFT)),
            ((14, CornerPositionEnum.UPPER_RIGHT), (11, CornerPositionEnum.LOWER_LEFT)),
        ]
        ComposedTemplate.__init__(self, _templates)
        for source, relpos, target in relative_positions:
            self.add_relation(source, relpos, target)
        for (start, start_corner), (end, end_corner) in pinned_corners:
            self.add_corner_relation((start, start_corner), (end, end_corner))
