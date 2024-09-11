from __future__ import annotations

import typing as ty

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
    arr = template.instantiate(plaquette_indices)
    for line in arr:
        for element in line:
            element = str(element) if element != 0 else "."
            print(f"{element:>3}", end="")
        print()
