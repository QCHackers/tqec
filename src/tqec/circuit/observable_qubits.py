from __future__ import annotations
from typing import Mapping, Sequence, Union

import cirq

from tqec.enums import TemplateOrientation
from tqec.exceptions import TQECException
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubit
from tqec.templates.base import Template


def observable_qubits_from_template(
    template: Template,
    plaquettes: Sequence[Plaquette] | Mapping[int, Plaquette],
    horizontal: TemplateOrientation = TemplateOrientation.HORIZONTAL,
) -> Sequence[tuple[cirq.GridQubit, int]]:
    """Return the default observable qubits for the given template and its plaquettes.

    Args:
        template (Template): The template to get the default observable qubits from.
        plaquettes (list[Plaquette] | dict[int, Plaquette]): The plaquettes to use to get the
        acurate positions of the observable qubits.
        horizontal (bool, optional): Whether to get the observable qubits from
            the horizontal or vertical midline. Defaults to True -> Horizontal.

    Raises:
        TQECException: If the number of plaquettes does not match the expected number.
        TQECException: If the plaquettes are provided as a dictionary and 0 is in the keys.
        TQECException: If the template does not have a definable midline.

    Returns:
        Sequence[tuple[cirq.GridQubit, int]]
    """
    if len(plaquettes) != template.expected_plaquettes_number:
        raise TQECException(
            f"{len(plaquettes)} plaquettes have been provided, but "
            f"{template.expected_plaquettes_number} were expected."
        )
    if isinstance(plaquettes, Mapping) and 0 in plaquettes:
        raise TQECException(
            "If using a dictionary, the input plaquettes parameter should not "
            f"contain the entry 0. Found a value ({plaquettes[0]}) at entry 0."
        )

    if isinstance(plaquettes, list):
        plaquettes = {i + 1: plaquette for i, plaquette in enumerate(plaquettes)}

    _indices = list(range(1, len(plaquettes) + 1))
    template_plaquettes = template.instantiate(_indices)
    increments = template.get_increments()

    try:
        midline_indices = template.get_midline_plaquettes(horizontal)
    except TQECException as e:
        raise TQECException(
            "The template does not have a midline. "
            "The observable qubits cannot be defined."
        ) from e

    observable_qubits = []
    for row_index, column_index in midline_indices:
        plaquette_index = template_plaquettes[row_index][column_index]
        if plaquette_index == 0:
            continue
        plaquette = plaquettes[plaquette_index]
        # GridQubits are indexed as (row, col), so (y, x)
        offset = (
            row_index * increments.y + plaquette.origin.y,
            column_index * increments.x + plaquette.origin.x,
        )
        observable_qubits += [
            (qubit.to_grid_qubit() + offset, 0)
            for qubit in _get_edge_qubits(plaquette, horizontal)
        ]
    return sorted(set(observable_qubits))


def _get_edge_qubits(
    plaquette: Plaquette,
    horizontal: TemplateOrientation = TemplateOrientation.HORIZONTAL,
) -> list[PlaquetteQubit]:
    def _get_relevant_value(qubit: PlaquetteQubit) -> int:
        return (
            qubit.position.y
            if horizontal == TemplateOrientation.HORIZONTAL
            else qubit.position.x
        )

    max_index = max(_get_relevant_value(q) for q in plaquette.qubits.data_qubits)
    return [
        qubit
        for qubit in plaquette.qubits.data_qubits
        if (_get_relevant_value(qubit) == max_index)
    ]
