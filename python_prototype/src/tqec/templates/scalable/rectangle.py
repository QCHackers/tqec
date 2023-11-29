from tqec.templates.base import Template
from tqec.templates.scalable.base import ScalableTemplate
from tqec.templates.shapes.rectangle import Rectangle
import typing as ty


class ScalableRectangle(ScalableTemplate):
    def __init__(
        self, width: int, height: int, scale_func: ty.Callable[[int], int] = lambda x: x
    ) -> None:
        super().__init__(Rectangle(width, height), scale_func)

    def scale_to(self, k: int) -> Template:
        # Get the actual scale
        new_dimension: int = self.get_scaled_scale(k)
        # Get the underlying rectangle shape parameters
        width, height = self.shape_instance.get_parameters()
        # Scale the parameters
        if width > height:
            width = new_dimension
        elif width == height:
            width = new_dimension
            height = new_dimension
        else:  # width < height
            height = new_dimension
        # Change the underlying rectangle shape parameters
        self.shape_instance.set_parameters((width, height))
        return self
