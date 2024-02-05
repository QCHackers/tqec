from tqec.templates.base import Template


class AtomicTemplate(Template):
    def __init__(
        self,
        default_x_increment: int = 2,
        default_y_increment: int = 2,
    ) -> None:
        """Base class for all the templates that are not composed of other Template instances.

        This class is the base of all templates that are "atomic", i.e., cannot be decomposed
        in other Template instances any further.

        The default increments define the distance between two plaquettes.
        For example a default_x_increment of 2 means that two 2x2 plaquettes will share
        a common edge.

        :param default_x_increment: default increment in the x direction between two plaquettes.
        :param default_y_increment: default increment in the y direction between two plaquettes.
        """
        super().__init__(default_x_increment, default_y_increment)
