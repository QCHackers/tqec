import typing as ty

import numpy

from tqec.position import Shape2D
from tqec.templates.base import Template
from tqec.templates.scale import ScalableShape2D
from tqec.templates.schemas import StackedTemplateModel


class StackedTemplate(Template):
    def __init__(
        self, default_x_increment: int = 2, default_y_increment: int = 2
    ) -> None:
        """A template composed of templates stacked on top of each others.

        This class implements a naive stack of Template instances. Each Template instance
        added to this class will be superposed on top of the previously added templates,
        potentially hiding parts of these.

        ## Warning
        This class does no effort to simplify the stack of templates. In particular, the
        plaquette indices that should be provided to the instanciate method are directly
        forwarded to the stacked templates, from bottom to top. If a stacked Template
        instance is hidding completly at least one kind of plaquette, this plaquette index
        should still be provided.

        ### Example
        Stacking the following template
        ```text
        1 2
        2 1
        ```
        on itself will require 4 (FOUR) template indices when calling `instanciate`:
        - the first 2 indices being forwarded to the bottom-most Template,
        - the last 2 indices being forwarded to the Template on top of it.

        The instanciation of such a stack using
        ```py
        stack.instanciate(1, 2, 3, 4)
        ```
        will return
        ```text
        3 4
        4 3
        ```
        as the last 2 indices (3 and 4) are forwarded to the top-most Template instance
        that hides the bottom one.
        """
        super().__init__(default_x_increment, default_y_increment)
        self._stack: list[Template] = []

    def push_template_on_top(
        self,
        template: Template,
    ) -> None:
        """Place a new template on the top of the stack.

        The new template can be offset by a certain amount, that might be scalable.

        :raises TQECException: if any of the specified offset coordinates is not positive.
        """
        self._stack.append(template)

    def pop_template_from_top(self) -> Template:
        """Removes the top-most template from the stack."""
        return self._stack.pop()

    def scale_to(self, k: int) -> "StackedTemplate":
        for t in self._stack:
            t.scale_to(k)
        return self

    @property
    def shape(self) -> Shape2D:
        shapex, shapey = 0, 0
        for template in self._stack:
            tshape = template.shape
            shapex = max(shapex, tshape.x)
            shapey = max(shapey, tshape.y)
        return Shape2D(shapex, shapey)

    @property
    def expected_plaquettes_number(self) -> int:
        return sum(t.expected_plaquettes_number for t in self._stack)

    def instantiate(self, plaquette_indices: ty.Sequence[int]) -> numpy.ndarray:
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

    def to_model(self) -> StackedTemplateModel:
        return StackedTemplateModel(
            default_increments=self._default_increments,
            stack=[t.to_model() for t in self._stack],
            tag="Stacked",
        )

    @property
    def scalable_shape(self) -> ScalableShape2D:
        """Returns the current template shape.

        Returns:
            the shape of the template.
        """
        raise NotImplementedError()
