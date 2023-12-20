from tqec.detectors.gate import ShiftCoordsGate
from tqec.detectors.transformer import fill_in_detectors_global_record_indices
from tqec.display import display
from tqec.constructions.qubit import ScalableQubitSquare
from tqec.plaquette.library import (
    XXXXPlaquette,
    ZZZZPlaquette,
    XXPlaquette,
    ZZPlaquette,
)
from tqec.enums import PlaquetteOrientation
from tqec.generation.circuit import generate_circuit
from tqec.noise_models import (
    XNoiseBeforeMeasurement,
    XNoiseAfterReset,
    MultiQubitDepolarizingNoiseAfterMultiQubitGate,
    DepolarizingNoiseOnIdlingQubit,
)
import cirq


def normalise_circuit(circuit: cirq.Circuit) -> cirq.Circuit:
    ordered_transformers = [
        cirq.drop_empty_moments,
    ]
    for transformer in ordered_transformers:
        circuit = transformer(circuit)
    return circuit


def to_noisy_circuit(circuit: cirq.Circuit) -> cirq.Circuit:
    noise_models = [
        XNoiseBeforeMeasurement(0.001),
        MultiQubitDepolarizingNoiseAfterMultiQubitGate(0.002),
        XNoiseAfterReset(0.003),
        DepolarizingNoiseOnIdlingQubit(0.004),
    ]
    for nm in noise_models:
        circuit = circuit.with_noise(nm)
    return circuit


repetitions: int = 100
code_distance: int = 3
dimension: int = code_distance - 1

template = ScalableQubitSquare(dimension)
plaquettes = [
    XXPlaquette(PlaquetteOrientation.UP),
    ZZPlaquette(PlaquetteOrientation.LEFT),
    XXXXPlaquette(),
    ZZZZPlaquette(),
    ZZPlaquette(PlaquetteOrientation.RIGHT),
    XXPlaquette(PlaquetteOrientation.DOWN),
]


def make_repeated_layer(circuit: cirq.Circuit) -> cirq.Circuit:
    any_qubit = next(iter(circuit.all_qubits()), None)
    assert (
        any_qubit is not None
    ), "Could not find any qubit in the given Circuit instance."
    circuit_to_repeat = cirq.Circuit([ShiftCoordsGate(0, 0, 1).on(any_qubit)]) + circuit
    repeated_circuit_operation = cirq.CircuitOperation(
        circuit_to_repeat.freeze()
    ).repeat(repetitions)
    return cirq.Circuit([repeated_circuit_operation])


layer_modificators = {1: make_repeated_layer}

display(template)
circuit = cirq.Circuit()
for layer_index in range(3):
    layer_circuit = generate_circuit(template, plaquettes, layer_index=layer_index)
    layer_circuit = normalise_circuit(layer_circuit)
    circuit += layer_modificators.get(layer_index, lambda circ: circ)(layer_circuit)

print(circuit)

circuit_with_detectors = fill_in_detectors_global_record_indices(circuit)

noisy_circuit = to_noisy_circuit(circuit_with_detectors)

# print(noisy_circuit)

from stimcirq import cirq_circuit_to_stim_circuit

stim_circuit = cirq_circuit_to_stim_circuit(noisy_circuit)
print(stim_circuit)
