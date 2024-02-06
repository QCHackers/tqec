from tqec.enums import ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF
from tqec.templates.atomic.rectangle import AlternatingRectangleTemplate
from tqec.templates.atomic.square import AlternatingSquareTemplate
from tqec.templates.base import TemplateWithIndices
from tqec.templates.composed import ComposedTemplate
from tqec.templates.scale import Dimension


class QubitSquareTemplate(ComposedTemplate):
    def __init__(self, dim: Dimension) -> None:
        """An error-corrected qubit.

        TODO
        """
        # nsone: non-scalable one
        nsone = Dimension(1, lambda _: 1)

        _templates = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithIndices(AlternatingSquareTemplate(dim), [3, 4]),
            # Top rectangle, containing plaquettes of type 1 only
            TemplateWithIndices(AlternatingRectangleTemplate(dim, nsone), [0, 1]),
            # Left rectangle, containing plaquettes of type 2 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, dim), [2, 0]),
            # Right rectangle, containing plaquettes of type 5 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, dim), [0, 5]),
            # Bottom rectangle, containing plaquettes of type 6 only
            TemplateWithIndices(AlternatingRectangleTemplate(dim, nsone), [6, 0]),
        ]
        _relations = [
            (1, ABOVE_OF, 0),
            (2, LEFT_OF, 0),
            (3, RIGHT_OF, 0),
            (4, BELOW_OF, 0),
        ]
        super().__init__(_templates)
        for source, relpos, target in _relations:
            self.add_relation(source, relpos, target)


class QubitRectangleTemplate(ComposedTemplate):
    def __init__(
        self,
        width: Dimension,
        height: Dimension,
    ) -> None:
        """A scalable rectangle error-corrected qubit.

        TODO
        """
        # nsone: non-scalable one
        nsone = Dimension(1, lambda _: 1)

        _templates = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithIndices(AlternatingRectangleTemplate(width, height), [3, 4]),
            # Top rectangle, containing plaquettes of type 1 only
            TemplateWithIndices(AlternatingRectangleTemplate(width, nsone), [0, 1]),
            # Left rectangle, containing plaquettes of type 2 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, height), [2, 0]),
            # Right rectangle, containing plaquettes of type 5 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, height), [0, 5]),
            # Bottom rectangle, containing plaquettes of type 6 only
            TemplateWithIndices(AlternatingRectangleTemplate(width, nsone), [6, 0]),
        ]
        _relations = [
            (1, ABOVE_OF, 0),
            (2, LEFT_OF, 0),
            (3, RIGHT_OF, 0),
            (4, BELOW_OF, 0),
        ]
        super().__init__(_templates)
        for source, relpos, target in _relations:
            self.add_relation(source, relpos, target)
