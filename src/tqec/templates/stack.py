import typing as ty

import numpy
from tqec.position import Shape2D
from tqec.templates.base import Template


class TemplateStack(Template):
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

    def scale_to(self, k: int) -> "TemplateStack":
        """Scales all the scalable templates in the stack to the given scale k.

        Note that this function scales to INLINE, so the instance on which it is called is
        modified in-place AND returned.

        :param k: the new scale of the component templates.
        :returns: self, once scaled.
        """
        for t in self._stack:
            t.scale_to(k)
        return self

    @property
    def shape(self) -> Shape2D:
        """Returns the current template shape.

        :returns: the numpy-like shape of the template.
        """
        shapex, shapey = 0, 0
        for template in self._stack:
            tshape = template.shape
            shapex = max(shapex, tshape.x)
            shapey = max(shapey, tshape.y)
        return Shape2D(shapex, shapey)

    def to_dict(self) -> dict[str, ty.Any]:
        """Returns a dict-like representation of the instance.

        Used to implement to_json.
        """
        return super().to_dict() | {
            "stack": {"templates": [t.to_dict() for t in self._stack]}
        }

    @property
    def expected_plaquettes_number(self) -> int:
        """Returns the number of plaquettes expected from the `instanciate` method.

        :returns: the number of plaquettes expected from the `instanciate` method.
        """
        return sum(t.expected_plaquettes_number for t in self._stack)

    def instanciate(self, *plaquette_indices: int) -> numpy.ndarray:
        """Generate the numpy array representing the template.

        :param plaquette_indices: the plaquette indices that will be forwarded to the
            underlying Shape instance's instanciate method.
        :returns: a numpy array with the given plaquette indices arranged according
            to the underlying shape of the template.
        """
        arr = numpy.zeros(self.shape.to_numpy_shape(), dtype=int)
        first_non_used_plaquette_index: int = 0
        for template in self._stack:
            istart = first_non_used_plaquette_index
            istop = istart + template.expected_plaquettes_number
            indices = [plaquette_indices[i] for i in range(istart, istop)]
            first_non_used_plaquette_index = istop

            tarr = template.instanciate(*indices)
            yshape, xshape = tarr.shape

            # We do not want "0" plaquettes (i.e., "no plaquette" with our convention) to
            # stack over and erase non-zero plaquettes.
            # To avoid that, we only replace on the non-zeros entries of the stacked over array.
            nonzeros = tarr.nonzero()
            arr[0:yshape, 0:xshape][nonzeros] = tarr[nonzeros]
        return arr
