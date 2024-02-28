# """Example taken from /notebooks/logical_qubit_memory_experiment.ipynb"""

import cirq

from tqec.detectors.operation import make_shift_coords
from tqec.enums import PlaquetteOrientation
from tqec.generation.circuit import generate_circuit
from tqec.plaquette.library import (
    MeasurementRoundedPlaquette,
    MeasurementSquarePlaquette,
    XXMemoryPlaquette,
    XXXXMemoryPlaquette,
    ZRoundedInitialisationPlaquette,
    ZSquareInitialisationPlaquette,
    ZZMemoryPlaquette,
    ZZZZMemoryPlaquette,
)
from tqec.plaquette.plaquette import Plaquette
from tqec.templates.constructions.qubit import QubitSquareTemplate
from tqec.templates.scale import Dimension, LinearFunction


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
    circuit_to_repeat = cirq.Circuit([make_shift_coords(0, 0, 1)]) + repeat_circuit
    repeated_circuit_operation = cirq.CircuitOperation(
        circuit_to_repeat.freeze()
    ).repeat(9)
    return cirq.Circuit([repeated_circuit_operation])


def _generate_circuit() -> cirq.Circuit:
    template = QubitSquareTemplate(Dimension(2, LinearFunction(2)))
    plaquettes: list[list[Plaquette]] = [
        [
            ZRoundedInitialisationPlaquette(PlaquetteOrientation.UP),
            XXMemoryPlaquette(
                PlaquetteOrientation.UP,
                [1, 2, 5, 6, 7, 8],
                include_detector=False,
                is_first_round=True,
            ),
            XXMemoryPlaquette(PlaquetteOrientation.UP, [1, 2, 5, 6, 7, 8]),
            MeasurementRoundedPlaquette(
                PlaquetteOrientation.UP, include_detector=False
            ),
        ],
        [
            ZRoundedInitialisationPlaquette(PlaquetteOrientation.LEFT),
            ZZMemoryPlaquette(
                PlaquetteOrientation.LEFT, [1, 5, 6, 8], is_first_round=True
            ),
            ZZMemoryPlaquette(PlaquetteOrientation.LEFT, [1, 5, 6, 8]),
            MeasurementRoundedPlaquette(PlaquetteOrientation.LEFT),
        ],
        [
            ZSquareInitialisationPlaquette(),
            XXXXMemoryPlaquette(
                [1, 2, 3, 4, 5, 6, 7, 8], include_detector=False, is_first_round=True
            ),
            XXXXMemoryPlaquette([1, 2, 3, 4, 5, 6, 7, 8]),
            MeasurementSquarePlaquette(include_detector=False),
        ],
        [
            ZSquareInitialisationPlaquette(),
            ZZZZMemoryPlaquette([1, 3, 4, 5, 6, 8], is_first_round=True),
            ZZZZMemoryPlaquette([1, 3, 4, 5, 6, 8]),
            MeasurementSquarePlaquette(),
        ],
        [
            ZRoundedInitialisationPlaquette(PlaquetteOrientation.RIGHT),
            ZZMemoryPlaquette(
                PlaquetteOrientation.RIGHT, [1, 3, 4, 8], is_first_round=True
            ),
            ZZMemoryPlaquette(PlaquetteOrientation.RIGHT, [1, 3, 4, 8]),
            MeasurementRoundedPlaquette(PlaquetteOrientation.RIGHT),
        ],
        [
            ZRoundedInitialisationPlaquette(PlaquetteOrientation.DOWN),
            XXMemoryPlaquette(
                PlaquetteOrientation.DOWN,
                [1, 2, 3, 4, 7, 8],
                include_detector=False,
                is_first_round=True,
            ),
            XXMemoryPlaquette(PlaquetteOrientation.DOWN, [1, 2, 3, 4, 7, 8]),
            MeasurementRoundedPlaquette(
                PlaquetteOrientation.DOWN, include_detector=False
            ),
        ],
    ]
    layer_modificators = {1: _make_repeated_layer}

    # 4. Actually create the cirq.Circuit instance by concatenating the circuits generated
    # for each layers and potentially modified by the modifiers defined above.
    circuit = cirq.Circuit()
    for layer_index in range(4):
        layer_circuit = generate_circuit(
            template,
            [plaquette_list[layer_index] for plaquette_list in plaquettes],
        )
        layer_circuit = _normalise_circuit(layer_circuit)
        circuit += layer_modificators.get(layer_index, lambda circ: circ)(layer_circuit)

    return circuit


def test_generate_circuit():
    """Minimal test to check that the circuit is generated correctly
    The target qubits are taken from the orginal notebook output.
    """
    generated_circuit = _generate_circuit()
    generate_qubits = [(q.row, q.col) for q in generated_circuit.all_qubits()]  # type: ignore
    target_qubits = [
        (6, 2),
        (3, 7),
        (3, 9),
        (1, 1),
        (10, 6),
        (8, 8),
        (1, 5),
        (2, 0),
        (6, 4),
        (2, 2),
        (6, 6),
        (1, 3),
        (7, 1),
        (7, 3),
        (4, 2),
        (1, 7),
        (7, 5),
        (1, 9),
        (7, 7),
        (2, 4),
        (6, 8),
        (9, 1),
        (2, 6),
        (9, 3),
        (9, 7),
        (4, 6),
        (4, 4),
        (7, 9),
        (5, 1),
        (5, 3),
        (2, 8),
        (9, 5),
        (5, 7),
        (8, 2),
        (0, 4),
        (9, 9),
        (3, 1),
        (4, 8),
        (5, 5),
        (3, 3),
        (4, 10),
        (3, 5),
        (10, 2),
        (8, 4),
        (5, 9),
        (8, 6),
        (0, 8),
        (6, 0),
        (8, 10),
    ]
    generate_qubits.sort()
    target_qubits.sort()
    assert generate_qubits == target_qubits
