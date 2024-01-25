from copy import deepcopy

import cirq

from tqec.generation.topology import get_plaquette_starting_index
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.schedule import ScheduledCircuit, merge_scheduled_circuits
from tqec.position import Shape2D
from tqec.templates.orchestrator import TemplateOrchestrator


def generate_circuit(
    template: TemplateOrchestrator,
    plaquettes: list[Plaquette],
) -> cirq.Circuit:
    """Generate a quantum circuit from a template and its plaquettes

    This is one of the core methods of the `tqec` package. It generates a quantum circuit
    from the description of the template that should be implemented as well as the plaquettes
    that should be used to instanciate the provided template.

    This function requires that a few pre-conditions on the inputs are met:
    1. the number of plaquettes provided should match the number of plaquettes required by
       the provided template.
    2. all the provided plaquettes should have the same shape.
    3. all the provided plaquettes should be implemented on cirq.GridQubit instances **only**.

    If any of the above pre-conditions is not met, the inputs are considered invalid, in which
    case this function **might** raise an error.

    :param template: spatial description of the quantum error correction experiment we want
        to implement.
    :param plaquettes: description of the computation that should happen at different time-slices
        of the quantum error correction experiment (or at least part of it).
    :returns: a cirq.Circuit instance implementing the (part of) quantum error correction experiment
        represented by the provided inputs.

    :raises AssertionError: if any of the pre-conditions is not met.
    """
    # Check that the user gave enough plaquettes.
    # The expected_plaquettes_number attribute includes the "no plaquette" indexed 0.
    # The user is not expected to know about this implementation detail, so we hide it.
    assert len(plaquettes) == template.expected_plaquettes_number - 1, (
        f"The given template requires {template.expected_plaquettes_number - 1} plaquettes "
        f"but only {len(plaquettes)} have been provided."
    )

    # Check that all the given plaquettes have the same shape. If not, this is an issue.
    # The shape limitation is an assumption to simplify the code and will have to be
    # eventually lifted.
    plaquette_shape: Shape2D = plaquettes[0].shape

    # Instanciate the template with the appropriate plaquette indices.
    # Index 0 is "no plaquette" by convention.
    _indices = list(range(len(plaquettes) + 1))
    template_plaquettes = template.instanciate(*_indices)
    # Plaquettes indices are starting at 1 in template_plaquettes. To avoid
    # offsets in the following code, we add an empty circuit at position 0.
    plaquette_circuits = [ScheduledCircuit(cirq.Circuit())] + [
        p.circuit for p in plaquettes
    ]
    # Assert that all the circuits are defined on 2-dimensional grids.
    assert all(
        isinstance(qubit, cirq.GridQubit)
        for circuit in plaquette_circuits
        for qubit in circuit.raw_circuit.all_qubits()
    ), "Qubits used in plaquette layers should be instances of cirq.GridQubit."

    # Generate the ScheduledCircuit instances for each plaquette instanciation
    all_scheduled_circuits: list[ScheduledCircuit] = []
    plaquette_index: int
    for plaquette_y, line in enumerate(template_plaquettes):
        for plaquette_x, plaquette_index in enumerate(line):
            qubit_x = get_plaquette_starting_index(plaquette_shape.x, plaquette_x)
            qubit_y = get_plaquette_starting_index(plaquette_shape.y, plaquette_y)
            scheduled_circuit = deepcopy(plaquette_circuits[plaquette_index])
            qubit_map = {
                # GridQubit are indexed as (row, col), so (y, x)
                qubit: qubit + (qubit_y, qubit_x)  # type: ignore
                for qubit in scheduled_circuit.raw_circuit.all_qubits()
            }
            scheduled_circuit.map_to_qubits(qubit_map, inplace=True)
            all_scheduled_circuits.append(scheduled_circuit)

    # Merge everything!
    return merge_scheduled_circuits(all_scheduled_circuits)
