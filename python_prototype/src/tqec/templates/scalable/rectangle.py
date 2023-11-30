from tqec.templates.base import Template
from tqec.templates.scalable.base import ScalableTemplate
from tqec.templates.shapes.rectangle import Rectangle


class ScalableRectangle(ScalableTemplate):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(Rectangle(width, height))

    def scale_to(self, k: int) -> Template:
        # Get the underlying rectangle shape parameters
        width, height = self.shape_instance.get_parameters()
        # Scale the parameters
        if width > height:
            width = k
        elif width == height:
            width = k
            height = k
        else:  # width < height
            height = k
        # Change the underlying rectangle shape parameters
        self.shape_instance.set_parameters((width, height))
        return self
