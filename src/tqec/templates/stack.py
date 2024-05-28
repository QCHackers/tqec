import typing as ty

import numpy

from tqec.enums import TemplateOrientation
from tqec.exceptions import TQECException
from tqec.position import Shape2D
from tqec.templates.base import Template
from tqec.templates.scale import ScalableShape2D


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
    def shape(self) -> ScalableShape2D:
        raise NotImplementedError()

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

    def get_midline_plaquettes(
        self, orientation: TemplateOrientation = TemplateOrientation.HORIZONTAL
    ) -> list[tuple[int, int]]:
        """We assumme the midline is defined by the template with the largest shape.
        This also assumes that operators are moved on the biggest template.
        """
        midline_shape = self.shape.y
        if orientation == TemplateOrientation.VERTICAL:
            midline_shape = self.shape.x
        if midline_shape % 2 == 1:
            raise TQECException(
                "Midline is not defined for odd "
                + f"{'height' if orientation == TemplateOrientation.HORIZONTAL else 'width'}."
            )
        for template in self._stack:
            if (
                orientation == TemplateOrientation.HORIZONTAL
                and template.shape.y == midline_shape
            ):
                return template.get_midline_plaquettes(orientation)
            if (
                orientation == TemplateOrientation.VERTICAL
                and template.shape.x == midline_shape
            ):
                return template.get_midline_plaquettes(orientation)
        raise TQECException(
            "No template with the expected midline shape was found in the stack."
        )
