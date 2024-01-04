import cirq

from tqec.generation.topology import get_plaquette_starting_index
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.schedule import ScheduledCircuit, merge_scheduled_circuits
from tqec.position import Shape2D
from tqec.templates.orchestrator import TemplateOrchestrator


def generate_circuit(
    template: TemplateOrchestrator,
    plaquettes: list[Plaquette],
    layer_index: int = 0,
) -> cirq.Circuit:
    # If no plaquettes are given, we only generate an empty circuit.
    if not plaquettes:
        return cirq.Circuit()

    # Check that all the given plaquettes have the same shape. If not, this is an issue.
    plaquette_shape: Shape2D = plaquettes[0].shape
    assert all(
        p.shape == plaquette_shape for p in plaquettes
    ), "All plaquettes should have exactly the same shape for the moment."

    # Compute the data that will be needed to generate the moments of the final circuit.
    _indices = list(range(len(plaquettes) + 1))
    template_plaquettes = template.instanciate(*_indices)
    # Plaquettes indices are starting at 1 in template_plaquettes. To avoid
    # offsets in the following code, we add an empty circuit at position 0.
    plaquette_circuits = [ScheduledCircuit(cirq.Circuit())] + [
        p.get_layer(layer_index) for p in plaquettes
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
    for y, line in enumerate(template_plaquettes):
        for x, plaquette_index in enumerate(line):
            qubit_x_index = get_plaquette_starting_index(plaquette_shape.x, x)
            qubit_y_index = get_plaquette_starting_index(plaquette_shape.y, y)
            scheduled_circuit = plaquette_circuits[plaquette_index].copy()
            qubit_map = {
                # GridQubit are indexed as (x, y)
                qubit: qubit + (qubit_x_index, qubit_y_index)
                for qubit in scheduled_circuit.raw_circuit.all_qubits()
            }
            scheduled_circuit.map_to_qubits(qubit_map, inplace=True)
            all_scheduled_circuits.append(scheduled_circuit)

    # Merge everything!
    return merge_scheduled_circuits(all_scheduled_circuits)
