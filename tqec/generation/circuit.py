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
    assert all(
        p.shape == plaquette_shape for p in plaquettes
    ), "All plaquettes should have exactly the same shape for the moment."

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
    all_scheduled_circuits: list[ScheduledCircuit] = list()
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
