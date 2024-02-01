from tqec.enums import ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF
from tqec.templates.base import TemplateWithIndices
from tqec.templates.orchestrator import TemplateOrchestrator
from tqec.templates.scalable.rectangle import ScalableRectangle
from tqec.templates.scalable.square import ScalableAlternatingSquare


class ScalableQubitSquare(TemplateOrchestrator):
    def __init__(self, k: int) -> None:
        """A scalable error-corrected qubit.

        The scale k of a **scalable template** is defined to be **half** the dimension/size
        of the **scalable axis** of the template. For example, a scalable 4x4 square has a
        scale of 2 for both its axis. This means the dimension/size of the scaled axis is
        enforced to be even, which avoids some invalid configuration of the template.

        ```text
        .  .  1  .  1  .
        2  3  4  3  4  .
        .  4  3  4  3  5
        2  3  4  3  4  .
        .  4  3  4  3  5
        .  6  .  6  .  .
        ```

        :param k: scale of the error-corrected qubit.
        """
        _templates = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithIndices(ScalableAlternatingSquare(2 * k), [3, 4]),
            # Top rectangle, containing plaquettes of type 1 only
            TemplateWithIndices(ScalableRectangle(2 * k, 1), [0, 1]),
            # Left rectangle, containing plaquettes of type 2 only
            TemplateWithIndices(ScalableRectangle(1, 2 * k), [2, 0]),
            # Right rectangle, containing plaquettes of type 5 only
            TemplateWithIndices(ScalableRectangle(1, 2 * k), [0, 5]),
            # Bottom rectangle, containing plaquettes of type 6 only
            TemplateWithIndices(ScalableRectangle(2 * k, 1), [6, 0]),
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
    def __init__(
        self, width: int, height: int, scale_width: bool | None = None
    ) -> None:
        """A scalable rectangle error-corrected qubit.

        A scalable rectangle qubit can only scale its width **or** height, but not both.

        ```text
        .  .  1  .  1  .  1  .
        2  3  4  3  4  3  4  .
        .  4  3  4  3  4  3  5
        2  3  4  3  4  3  4  .
        .  4  3  4  3  4  3  5
        .  6  .  6  .  6  .  .
        ```

        :param width: width of the qubit.
        :param height: height of the qubit.
        :param scale_width: whether to scale the width or height. If None, the dimension
            with the even value or the larger value will be scaled. If both dimensions
            are even and equal, the width will be scaled by default.
        """
        _templates = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithIndices(ScalableRectangle(width, height, scale_width), [3, 4]),
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
