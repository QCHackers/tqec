import typing as ty

import numpy
from tqec.position import Shape2D
from tqec.templates.base import Template


class StackedTemplate(Template):
    def __init__(
        self, default_x_increment: int = 2, default_y_increment: int = 2
    ) -> None:
        """A template composed of templates stacked on top of each others.

        This class implements a naive stack of ``Template`` instances. Each
        ``Template`` instance added to this class will be superposed on top
        of the previously added templates, potentially hiding parts of these.

        Warning:
            This class does no effort to simplify the stack of templates. In
            particular, the plaquette indices that should be provided to the
            ``instantiate`` method are directly forwarded to the stacked templates,
            from bottom to top. If a stacked ``Template`` instance is hidding
            completly at least one kind of plaquette, this plaquette index
            should still be provided.

            Example:

                Stacking the following template
                ```text
                1 2
                2 1
                ```
                on itself will require 4 (FOUR) template indices when calling
                ``instantiate``:
                - the first 2 indices being forwarded to the bottom-most ``Template``,
                - the last 2 indices being forwarded to the ``Template`` on top of it.

                The instantiation of such a stack using
                ```py
                stack.instantiate(1, 2, 3, 4)
                ```
                will return
                ```text
                3 4
                4 3
                ```
                as the last 2 indices (3 and 4) are forwarded to the top-most ``Template``
                instance that hides the bottom one.
        """
        super().__init__(default_x_increment, default_y_increment)
        self._stack: list[Template] = []

    def push_template_on_top(
        self,
        template: Template,
    ) -> None:
        """Place a new template on the top of the stack."""
        self._stack.append(template)

    def pop_template_from_top(self) -> Template:
        """Remove the top-most template from the stack."""
        return self._stack.pop()

    def scale_to(self, k: int) -> "StackedTemplate":
        """Scale all the scalable templates in the stack to the given scale k.

        Note:
            This function scales to INLINE, so the instance on which it is
            called is modified in-place AND returned.

        Args:
            k: the new scale of the component templates.

        Returns:
            self, once scaled.
        """
        for t in self._stack:
            t.scale_to(k)
        return self

    @property
    def shape(self) -> Shape2D:
        """Return the current template shape."""
        shapex, shapey = 0, 0
        for template in self._stack:
            tshape = template.shape
            shapex = max(shapex, tshape.x)
            shapey = max(shapey, tshape.y)
        return Shape2D(shapex, shapey)

    def to_dict(self) -> dict[str, ty.Any]:
        """Return a dict-like representation of the instance."""
        return super().to_dict() | {
            "stack": {"templates": [t.to_dict() for t in self._stack]}
        }

    @property
    def expected_plaquettes_number(self) -> int:
        """Returns the number of plaquettes expected from the ``instantiate`` method."""
        return sum(t.expected_plaquettes_number for t in self._stack)

    def instantiate(self, plaquette_indices: ty.Sequence[int]) -> numpy.ndarray:
        """Generate the numpy array representing the template.

        Args:
            plaquette_indices: the plaquette indices that will be forwarded to
                the stacked ``Template`` instances.

        Returns:
            a numpy array with the given plaquette indices arranged according
            to the stack of ``Template`` instances stored.
        """
        self._check_plaquette_number(plaquette_indices, self.expected_plaquettes_number)
        arr = numpy.zeros(self.shape.to_numpy_shape(), dtype=int)
        first_non_used_plaquette_index: int = 0
        for template in self._stack:
            istart = first_non_used_plaquette_index
            istop = istart + template.expected_plaquettes_number
            indices = [plaquette_indices[i] for i in range(istart, istop)]
            first_non_used_plaquette_index = istop

            tarr = template.instantiate(indices)
            yshape, xshape = tarr.shape

            # We do not want "0" plaquettes (i.e., "no plaquette" with our convention) to
            # stack over and erase non-zero plaquettes.
            # To avoid that, we only replace on the non-zeros entries of the stacked over array.
            nonzeros = tarr.nonzero()
            arr[0:yshape, 0:xshape][nonzeros] = tarr[nonzeros]
        return arr
