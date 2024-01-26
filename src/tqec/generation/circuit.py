from copy import deepcopy

import cirq

from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.schedule import ScheduledCircuit, merge_scheduled_circuits
from tqec.position import Position
from tqec.templates.orchestrator import TemplateOrchestrator


def generate_circuit(
    template: TemplateOrchestrator,
    plaquettes: list[Plaquette],
    default_x_increment: int = 2,
    default_y_increment: int = 2,
) -> cirq.Circuit:
    """Generate a quantum circuit from a template and its plaquettes

    This is one of the core methods of the `tqec` package. It generates a quantum circuit
    from the description of the template that should be implemented as well as the plaquettes
    that should be used to instanciate the provided template.

    This function requires that a few pre-conditions on the inputs are met:
    1. the number of plaquettes provided should match the number of plaquettes required by
       the provided template.
    2. all the provided plaquettes are rectengular. For '0' plaquettes, the shape is asumed to be
        (default_x_increment, default_y_increment).
    3. all the provided plaquettes should be implemented on cirq.GridQubit instances **only**.

    If any of the above pre-conditions is not met, the inputs are considered invalid, in which
    case this function **might** raise an error.

    :param template: spatial description of the quantum error correction experiment we want
        to implement.
    :param plaquettes: description of the computation that should happen at different time-slices
        of the quantum error correction experiment (or at least part of it).
    :param default_x_increment: default increment in the x direction between two plaquettes.
    :param default_y_increment: default increment in the y direction between two plaquettes.

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
            scheduled_circuit = deepcopy(plaquette_circuits[plaquette_index])

            offset: Position = _find_offset(
                all_scheduled_circuits,
                plaquette_y,
                plaquette_x,
                len(line),
                default_x_increment,
                default_y_increment,
            )
            print(offset)
            if plaquette_index > 0:
                plaquette = plaquettes[plaquette_index - 1]
                qubit_map = _create_mapping(plaquette, scheduled_circuit, offset)
                scheduled_circuit.map_to_qubits(qubit_map, inplace=True)
            all_scheduled_circuits.append(scheduled_circuit)

    # Merge everything!
    return merge_scheduled_circuits(all_scheduled_circuits)


def _create_mapping(
    plaquette: Plaquette,
    scheduled_circuit: ScheduledCircuit,
    offset: Position,
) -> dict[cirq.Qid, cirq.Qid]:
    origin = plaquette.origin
    assert origin == Position(0, 0), "Only origin (0,0) is supported for now"

    qubit_map = {
        # GridQubit are indexed as (row, col), so (y, x)
        # Qubits are given relative to an origin, so we need to add the offset
        qubit: qubit + (offset.y, offset.x) + (origin.y, origin.x)  # type: ignore
        for qubit in scheduled_circuit.raw_circuit.all_qubits()
    }
    return qubit_map


def _find_offset(
    scheduled_circuits: list[ScheduledCircuit],
    row_index: int,
    column_index: int,
    length: int,
    default_x_increment: int,
    default_y_increment: int,
) -> Position:
    """Computes the offset by looking at already placed circuits

    We anchor the top left corner by one of the following ways:
        - at the origin (0,0) (first circuit)
        - the top right corner of the previous circuit (left)
        - the bottom left corner of the previous circuit (above)
        - the bottom ove the above and the right of the left (above and left)
    """
    # first circuit
    if len(scheduled_circuits) == 0 or row_index == column_index == 0:
        return Position(0, 0)
    default_multiplier = 0
    for circuit in scheduled_circuits[: -(column_index + 1) : -1]:
        if len(circuit.raw_circuit.all_qubits()) == 0:
            default_multiplier += 1
        else:
            position_left = _find_coordinate(circuit, above=False)
            position_left.x += default_x_increment * default_multiplier
            break
    else:
        position_left = Position(default_x_increment * default_multiplier, 0)

    if row_index == 0:  # left
        return Position(position_left.x, 0)

    default_multiplier = 0
    for circuit in reversed(scheduled_circuits[column_index::length]):
        if len(circuit.raw_circuit.all_qubits()) == 0:
            default_multiplier += 1
        else:
            position_above = _find_coordinate(circuit, above=True)
            position_above.y += default_y_increment * default_multiplier
            break
    else:
        position_above = Position(0, default_y_increment * default_multiplier)

    if column_index == 0:  # above
        return position_above
    if position_left == position_above:
        return position_left
    return Position(position_left.x, position_above.y)


def _find_coordinate(final_circuit: ScheduledCircuit, above: bool = False) -> Position:
    if len(final_circuit.raw_circuit.all_qubits()) == 0:
        return Position(0, 0)
    position = max(
        (
            Position(qubit.col, qubit.row)
            for qubit in final_circuit.raw_circuit.all_qubits()
        ),
        key=lambda p: (p.y, -p.x) if above else (p.x, -p.y),
    )
    return Position(position.x, position.y)
