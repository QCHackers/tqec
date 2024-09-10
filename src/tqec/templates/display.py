from __future__ import annotations

import typing as ty

import numpy
import numpy.typing as npt

from tqec.templates.base import Template


def display_template(
    template: Template, plaquette_indices: ty.Sequence[int] | None = None
) -> None:
    """Display a template instance with ASCII output.

    Args:
        template: the Template instance to display.
        plaquette_indices: the plaquette indices that are forwarded to the call
            to `template.instantiate` to get the actual template representation.
            If None, default to ``range(1, template.expected_plaquettes_number + 1)``.
    """
    if plaquette_indices is None:
        plaquette_indices = tuple(range(1, template.expected_plaquettes_number + 1))
    display_template_from_instantiation(template.instantiate(plaquette_indices))


def display_template_from_instantiation(instantiation: npt.NDArray[numpy.int_]) -> None:
    """Display an array representing a template instantiation with ASCII
    output.

    Args:
        instantiation: the integer array obtained from the `Template.instantiate`
            method.
    """
    for line in instantiation:
        for element in line:
            element = str(element) if element != 0 else "."
            print(f"{element:>3}", end="")
        print()
