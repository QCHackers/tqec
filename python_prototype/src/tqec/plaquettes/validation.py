"""Plaquette validation functions."""

from tqec.enums import TemplateRelativePositionEnum
from .plaquettes import Plaquette


def plaquettes_are_valid(
    first: Plaquette, second: Plaquette, position: TemplateRelativePositionEnum
) -> bool:
    """Check if a two plaquettes are mutually valid.

    TODO generate list of qubits to compare from positionioning.
    Args:
        first (Plaquette): The first plaquette.
        second (Plaquette): The second plaquette.
        position (TemplateRelativePositionEnum): The relative position of the second plaquette.

    Returns:
        bool: True if the plaquettes are valid.
    """
    self_qubits: list[int] = []
    other_qubits: list[int] = []
    return first.commutes(second) and first.circuits_match(
        second, self_qubits, other_qubits
    )
