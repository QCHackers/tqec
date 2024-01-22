from tqec.enums import ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF
from tqec.templates.base import TemplateWithIndices
from tqec.templates.orchestrator import TemplateOrchestrator
from tqec.templates.scalable.rectangle import ScalableRectangle
from tqec.templates.scalable.square import ScalableAlternatingSquare


class ScalableQubitSquare(TemplateOrchestrator):
    def __init__(self, dim: int) -> None:
        """A scalable error-corrected qubit.

        ```text
        .  .  1  .  1  .
        2  3  4  3  4  .
        .  4  3  4  3  5
        2  3  4  3  4  .
        .  4  3  4  3  5
        .  6  .  6  .  .
        ```

        :param dim: dimension (code distance - 1) of the error-corrected qubit.
        """
        _templates = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithIndices(ScalableAlternatingSquare(dim), [3, 4]),
            # Top rectangle, containing plaquettes of type 1 only
            TemplateWithIndices(ScalableRectangle(dim, 1), [0, 1]),
            # Left rectangle, containing plaquettes of type 2 only
            TemplateWithIndices(ScalableRectangle(1, dim), [2, 0]),
            # Right rectangle, containing plaquettes of type 5 only
            TemplateWithIndices(ScalableRectangle(1, dim), [0, 5]),
            # Bottom rectangle, containing plaquettes of type 6 only
            TemplateWithIndices(ScalableRectangle(dim, 1), [6, 0]),
        ]
        _relations = [
            (1, ABOVE_OF, 0),
            (2, LEFT_OF, 0),
            (3, RIGHT_OF, 0),
            (4, BELOW_OF, 0),
        ]
        TemplateOrchestrator.__init__(self, _templates)
        for source, relpos, target in _relations:
            self.add_relation(source, relpos, target)


class ScalableQubitRectangle(TemplateOrchestrator):
    def __init__(self, width: int, height: int) -> None:
        _templates = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithIndices(ScalableRectangle(width, height), [3, 4]),
            # Top rectangle, containing plaquettes of type 1 only
            TemplateWithIndices(ScalableRectangle(width, 1), [0, 1]),
            # Left rectangle, containing plaquettes of type 2 only
            TemplateWithIndices(ScalableRectangle(1, height), [2, 0]),
            # Right rectangle, containing plaquettes of type 5 only
            TemplateWithIndices(ScalableRectangle(1, height), [0, 5]),
            # Bottom rectangle, containing plaquettes of type 6 only
            TemplateWithIndices(ScalableRectangle(width, 1), [6, 0]),
        ]
        _relations = [
            (1, ABOVE_OF, 0),
            (2, LEFT_OF, 0),
            (3, RIGHT_OF, 0),
            (4, BELOW_OF, 0),
        ]
        TemplateOrchestrator.__init__(self, _templates)
        for source, relpos, target in _relations:
            self.add_relation(source, relpos, target)
