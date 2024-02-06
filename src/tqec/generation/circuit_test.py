"""Example taken from /notebooks/logical_qubit_memory_experiment.ipynb"""

import cirq
from tqec.detectors.gate import ShiftCoordsGate
from tqec.enums import PlaquetteOrientation
from tqec.generation.circuit import generate_circuit
from tqec.plaquette.library import (
    XXPlaquetteList,
    XXXXPlaquetteList,
    ZZPlaquetteList,
    ZZZZPlaquetteList,
)
from tqec.plaquette.plaquette import PlaquetteList
from tqec.templates.constructions.qubit import QubitSquareTemplate


def _normalise_circuit(norm_circuit: cirq.Circuit) -> cirq.Circuit:
    ordered_transformers = [
        cirq.drop_empty_moments,
    ]
    for transformer in ordered_transformers:
        norm_circuit = transformer(norm_circuit)
    return norm_circuit


def _make_repeated_layer(repeat_circuit: cirq.Circuit) -> cirq.Circuit:
    # Note: we do not care on which qubit it is applied, but we want a SHIFT_COORDS instruction
    #       to be inserted somewhere in the repetition loop. It is inserted at the beginning.
    any_qubit = next(iter(repeat_circuit.all_qubits()), None)
    assert (
        any_qubit is not None
    ), "Could not find any qubit in the given Circuit instance."
    circuit_to_repeat = (
        cirq.Circuit([ShiftCoordsGate(0, 0, 1).on(any_qubit)]) + repeat_circuit
    )
    repeated_circuit_operation = cirq.CircuitOperation(
        circuit_to_repeat.freeze()
    ).repeat(9)
    return cirq.Circuit([repeated_circuit_operation])


def _generate_circuit() -> cirq.Circuit:
    template = QubitSquareTemplate(2)
    plaquettes: list[PlaquetteList] = [
        XXPlaquetteList(
            PlaquetteOrientation.UP, [1, 2, 5, 6, 7, 8], include_detector=False
        ),
        ZZPlaquetteList(PlaquetteOrientation.LEFT, [1, 5, 6, 8]),
        XXXXPlaquetteList([1, 2, 3, 4, 5, 6, 7, 8], include_detector=False),
        ZZZZPlaquetteList([1, 3, 4, 5, 6, 8]),
        ZZPlaquetteList(PlaquetteOrientation.RIGHT, [1, 3, 4, 8]),
        XXPlaquetteList(
            PlaquetteOrientation.DOWN, [1, 2, 3, 4, 7, 8], include_detector=False
        ),
    ]

    layer_modificators = {1: _make_repeated_layer}

    # 4. Actually create the cirq.Circuit instance by concatenating the circuits generated
    # for each layers and potentially modified by the modifiers defined above.
    circuit = cirq.Circuit()
    for layer_index in range(3):
        layer_circuit = generate_circuit(
            template,
            [plaquette_list.plaquettes[layer_index] for plaquette_list in plaquettes],
        )
        layer_circuit = _normalise_circuit(layer_circuit)
        circuit += layer_modificators.get(layer_index, lambda circ: circ)(layer_circuit)

    return circuit


def test_generate_circuit():
    """Minimal test to check that the circuit is generated correctly
    The target qubits are taken from the orginal notebook output.
    """
    generated_circuit = _generate_circuit()
    generate_qubits = [(q.row, q.col) for q in generated_circuit.all_qubits()]
    target_qubits = [
        (7, 3),
        (6, 6),
        (4, 4),
        (5, 5),
        (2, 2),
        (6, 2),
        (5, 3),
        (4, 6),
        (5, 7),
        (6, 4),
        (2, 6),
        (3, 5),
        (3, 1),
        (1, 5),
        (3, 3),
        (2, 4),
        (4, 2),
    ]
    generate_qubits.sort()
    target_qubits.sort()
    assert generate_qubits == target_qubits
