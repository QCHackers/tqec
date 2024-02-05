from copy import copy

from tqec.enums import ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF
from tqec.exceptions import TQECException
from tqec.templates.atomic.rectangle import AlternatingRectangleTemplate
from tqec.templates.atomic.square import AlternatingSquareTemplate
from tqec.templates.base import TemplateWithIndices
from tqec.templates.composed import ComposedTemplate
from tqec.templates.scale import Dimension


class QubitSquareTemplate(ComposedTemplate):
    def __init__(self, k: int | Dimension) -> None:
        """An error-corrected qubit.

        TODO
        """
        # sdim: scalable dimension
        sdim: Dimension
        if isinstance(k, int):
            sdim = Dimension(k, scaling_function=lambda scale: 2 * scale)
        else:
            sdim = copy(k)
        sdim.value = 2 * sdim.value
        # nsone: non-scalable one
        nsone = Dimension(1, is_fixed=True)

        _templates = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithIndices(AlternatingSquareTemplate(sdim), [3, 4]),
            # Top rectangle, containing plaquettes of type 1 only
            TemplateWithIndices(AlternatingRectangleTemplate(sdim, nsone), [0, 1]),
            # Left rectangle, containing plaquettes of type 2 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, sdim), [2, 0]),
            # Right rectangle, containing plaquettes of type 5 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, sdim), [0, 5]),
            # Bottom rectangle, containing plaquettes of type 6 only
            TemplateWithIndices(AlternatingRectangleTemplate(sdim, nsone), [6, 0]),
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


class ScalableQubitRectangle(ComposedTemplate):
    def __init__(
        self,
        k_width: int | Dimension,
        k_height: int | Dimension,
        scale_width: bool | None = None,
    ) -> None:
        """A scalable rectangle error-corrected qubit.

        TODO
        """
        swidth, sheight = self.get_dimensions(k_width, k_height, scale_width)
        # nsone: non-scalable one
        nsone = Dimension(1, is_fixed=True)

        _templates = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithIndices(AlternatingRectangleTemplate(swidth, sheight), [3, 4]),
            # Top rectangle, containing plaquettes of type 1 only
            TemplateWithIndices(AlternatingRectangleTemplate(swidth, nsone), [0, 1]),
            # Left rectangle, containing plaquettes of type 2 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, sheight), [2, 0]),
            # Right rectangle, containing plaquettes of type 5 only
            TemplateWithIndices(AlternatingRectangleTemplate(nsone, sheight), [0, 5]),
            # Bottom rectangle, containing plaquettes of type 6 only
            TemplateWithIndices(AlternatingRectangleTemplate(swidth, nsone), [6, 0]),
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

    @staticmethod
    def get_dimensions(
        k_width: int | Dimension,
        k_height: int | Dimension,
        scale_width: bool | None = None,
    ) -> tuple[Dimension, Dimension]:
        if (
            isinstance(k_width, Dimension)
            and isinstance(k_height, Dimension)
            and scale_width is None
        ):
            width, height = copy(k_width), copy(k_height)
            width.value, height.value = 2 * width.value, 2 * height.value
            return width, height
        elif isinstance(k_width, int) and isinstance(k_height, int):
            width, height = 2 * k_width, 2 * k_height
            # Determine which dimension to scale if scale_width is not provided.
            if scale_width is None:
                scale_width = width >= height
            if scale_width:
                return Dimension(width, scaling_function=lambda k: 2 * k), Dimension(
                    height, is_fixed=True
                )
            else:
                return Dimension(width, is_fixed=True), Dimension(
                    height, scaling_function=lambda k: 2 * k
                )
        else:
            raise TQECException(
                f"Wrong dimensions types. You gave {type(k_width).__name__}, "
                f"{type(k_height).__name__}, {str(scale_width)}. "
                "Refer to the documentation."
            )
