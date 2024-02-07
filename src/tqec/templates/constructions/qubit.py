from tqec.enums import ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF
from tqec.templates.atomic.rectangle import AlternatingRectangleTemplate
from tqec.templates.atomic.square import AlternatingSquareTemplate
from tqec.templates.base import TemplateWithIndices
from tqec.templates.composed import ComposedTemplate
from tqec.templates.scale import Dimension, LinearFunction


class QubitSquareTemplate(ComposedTemplate):
    def __init__(self, dim: Dimension) -> None:
        """An error-corrected qubit.

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

        Args:
            k: scale of the error-corrected qubit.
        """
        # nsone: non-scalable one
        nsone = Dimension(1, LinearFunction(0, 1))

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

        A scalable rectangle qubit can only scale its width **or** height, but not both.
        ```text
        .  .  1  .  1  .  1  .
        2  3  4  3  4  3  4  .
        .  4  3  4  3  4  3  5
        2  3  4  3  4  3  4  .
        .  4  3  4  3  4  3  5
        .  6  .  6  .  6  .  .
        ```

        Args:
            k_width: half the width of the qubit.
            k_height: half the height of the qubit.
            scale_width: whether to scale the width or height. If None, the
                dimension with the larger value will be scaled. If both
                dimensions are equal, the width will be scaled by default.
        """
        # nsone: non-scalable one
        nsone = Dimension(1, LinearFunction(0, 1))

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
