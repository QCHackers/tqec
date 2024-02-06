from tqec.enums import ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF, CornerPositionEnum
from tqec.templates.atomic.rectangle import (
    AlternatingRectangleTemplate,
    RawRectangleTemplate,
)
from tqec.templates.atomic.square import (
    AlternatingCornerSquareTemplate,
    AlternatingSquareTemplate,
)
from tqec.templates.base import TemplateWithIndices
from tqec.templates.composed import ComposedTemplate
from tqec.templates.scale import Dimension


class ScalableCorner(ComposedTemplate):
    def __init__(self, dim: Dimension) -> None:
        """A scalable corner template.

        TODO
        """
        # nsone: non-scalable one
        # nstwo: non-scalable two
        nsone = Dimension(1, lambda _: 1)
        nstwo = Dimension(2, lambda _: 2)

        _templates = [
            # 0
            TemplateWithIndices(AlternatingRectangleTemplate(dim, nsone), [0, 1]),
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, dim), [2, 0]),
            TemplateWithIndices(AlternatingSquareTemplate(dim), [3, 4]),
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, dim), [0, 5]),
            TemplateWithIndices(RawRectangleTemplate([[0]]), [2]),
            # 5
            TemplateWithIndices(AlternatingRectangleTemplate(dim, nstwo), [3, 4]),
            TemplateWithIndices(RawRectangleTemplate([[0]]), [6]),
            TemplateWithIndices(AlternatingRectangleTemplate(dim, nsone), [7, 0]),
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, dim), [2, 0]),
            TemplateWithIndices(
                AlternatingCornerSquareTemplate(dim, CornerPositionEnum.LOWER_LEFT),
                [
                    3,
                    4,
                    8,
                    9,
                    11,
                ],
            ),
            # 10
            TemplateWithIndices(AlternatingRectangleTemplate(nstwo, dim), [9, 8]),
            TemplateWithIndices(AlternatingSquareTemplate(dim), [9, 8]),
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, dim), [10, 0]),
            TemplateWithIndices(AlternatingRectangleTemplate(dim, nsone), [0, 12]),
            TemplateWithIndices(RawRectangleTemplate([[0]]), [12]),
            # 15
            TemplateWithIndices(AlternatingRectangleTemplate(dim, nsone), [0, 12]),
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
