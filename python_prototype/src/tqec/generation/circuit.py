from tqec.generation.topology import get_plaquette_starting_index
from tqec.plaquette.plaquette import Plaquette
from tqec.position import Shape2D
from tqec.templates.base import Template
from tqec.templates.orchestrator import TemplateOrchestrator

import cirq
from cirq.ops.raw_types import Qid
from cirq.circuits.circuit import Circuit
from cirq.circuits.moment import Moment
from cirq import GridQubit


def map_moment_to_qubits(moment: Moment, qubit_map: dict[Qid, Qid]) -> Moment:
    return moment.transform_qubits(qubit_map)


def generate_circuit(
    template: Template | TemplateOrchestrator,
    plaquettes: list[Plaquette],
    layer_index: int = 0,
) -> Circuit:
    # If no plaquettes are given, we only generate an empty circuit.
    if not plaquettes:
        return Circuit()

    # Check that all the given plaquettes have the same shape. If not, this is an issue.
    plaquette_shape: Shape2D = plaquettes[0].shape
    assert all(
        p.shape == plaquette_shape for p in plaquettes
    ), "All plaquettes should have exactly the same shape for the moment."

    # Compute the data that will be needed to generate the moments of the final circuit.
    _indices = list(range(1, len(plaquettes) + 1))
    template_plaquettes = template.instanciate(*_indices)
    # Plaquettes indices are starting at 1 in template_plaquettes. To avoid
    # offsets in the following code, we add an empty circuit at position 0.
    plaquette_circuits = [Circuit()] + [p.get_layer(layer_index) for p in plaquettes]
    # Assert that all the circuits are defined on 2-dimensional grids.
    assert all(
        isinstance(qubit, GridQubit)
        for circuit in plaquette_circuits
        for qubit in circuit.all_qubits()
    ), "Qubits used in plaquette layers should be instances of cirq.GridQubit."

    # Compute the number of moment that will be needed for the final circuit.
    number_of_moments: int = max(len(circ.moments) for circ in plaquette_circuits)

    final_moments: list[Moment] = []

    for moment_index in range(number_of_moments):
        # Recover all the operations that need to happen at this moment and
        # map them to the correct qubits.
        operations: list[cirq.ops.Operation] = []
        for y, line in enumerate(template_plaquettes):
            for x, plaquette_index in enumerate(line):
                current_circuit = plaquette_circuits[plaquette_index]
                current_template_moment: Moment = current_circuit[moment_index]
                qubit_x_index = get_plaquette_starting_index(plaquette_shape.x, x)
                qubit_y_index = get_plaquette_starting_index(plaquette_shape.y, y)
                qubit_map = {
                    qubit: qubit + (qubit_y_index, qubit_x_index)
                    for qubit in current_template_moment.qubits
                }
                operations.extend(
                    map_moment_to_qubits(current_template_moment, qubit_map=qubit_map)
                )
        # We now have all the operations of this specific moment, create it.
        final_moments.append(Moment.from_ops(*operations))
    return Circuit(final_moments)
