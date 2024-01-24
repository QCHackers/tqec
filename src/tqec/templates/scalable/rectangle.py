from tqec.templates.base import Template
from tqec.templates.scalable.base import DimensionNotEven, ScalableTemplate
from tqec.templates.shapes.rectangle import Rectangle


class ScalableRectangle(ScalableTemplate):
    def __init__(
        self,
        width: int,
        height: int,
        scale_width: bool | None = None,
    ) -> None:
        """Rectangle with scalable width **or** height.

        A scalable rectangle can only scale its width **or** height, but not both.

        :param width: width of the rectangle.
        :param height: height of the rectangle.
        :param scale_width: whether to scale the width or height. If None, the dimension
            with the even value or the larger value will be scaled. If both dimensions
            are even and equal, the width will be scaled by default.
        :raises DimensionNotEven: if both width and height are odd numbers.
        """
        if width % 2 != 0 and height != 0:
            raise DimensionNotEven(width, height)

        # Determine which dimension to scale
        if scale_width is None:
            scale_width = height % 2 != 0 or (width % 2 == 0 and width >= height)
        super().__init__(Rectangle(width, height))
        self._scale_width: bool = scale_width

    def scale_to(self, k: int) -> Template:
        # Get the underlying rectangle shape parameters
        width, height = self.shape_instance.get_parameters()
        # Scale the parameters
        if self._scale_width:
            width = 2 * k
        else:
            height = 2 * k
        # Change the underlying rectangle shape parameters
        self.shape_instance.set_parameters((width, height))
        return self
