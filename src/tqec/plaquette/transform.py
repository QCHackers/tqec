"""Utility functions for transforming the plaquettes."""

from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubits


def project_on_boundary(
    plaquette: Plaquette, projected_orientation: PlaquetteOrientation
) -> Plaquette:
    """Project the plaquette on boundary and return a new plaquette with the
    remaining qubits and circuit.

    This method is useful for deriving a boundary plaquette from a integral
    plaquette.

    Args:
        plaquette: the plaquette to project.
        projected_orientation: the orientation of the plaquette after the
            projection.

    Returns:
        A new plaquette with projected qubits and circuit. The qubits are
        updated to only keep the qubits on the side complementary to the
        provided orientation. The circuit is also updated to only use the
        kept qubits and empty moments with the corresponding schedules are
        removed.
    """
    kept_data_qubits = plaquette.qubits.get_qubits_on_side(
        projected_orientation.to_plaquette_side()
    )
    new_plaquette_qubits = PlaquetteQubits(
        kept_data_qubits, plaquette.qubits.syndrome_qubits
    )
    new_scheduled_circuit = plaquette.circuit.filter_by_qubits(
        new_plaquette_qubits.all_qubits
    )
    return Plaquette(
        new_plaquette_qubits, new_scheduled_circuit, plaquette.mergeable_instructions
    )
