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

from tqec.generation.transformers import (
    merge_adjacent_measurements,
    merge_adjacent_resets,
    remove_mergeable_tag,
)
from tqec.noise_models import (
    XNoiseBeforeMeasurement,
    XNoiseAfterReset,
    MultiQubitDepolarizingNoiseAfterMultiQubitGate,
    DepolarizingNoiseOnIdlingQubit,
)
import cirq


def normalise_circuit(circuit: cirq.Circuit) -> cirq.Circuit:
    ordered_transformers = [
        cirq.synchronize_terminal_measurements,
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
code_distance: int = 5
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

layer_modificators = {
    1: lambda circ: cirq.CircuitOperation(circ.freeze()).repeat(repetitions)
}

# display(template)
circuit = cirq.Circuit()
for layer_index in range(3):
    layer_circuit = generate_circuit(template, plaquettes, layer_index=layer_index)
    layer_circuit = normalise_circuit(layer_circuit)
    circuit += layer_modificators.get(layer_index, lambda circ: circ)(layer_circuit)

print(circuit)

noisy_circuit = to_noisy_circuit(circuit)

# print(noisy_circuit)

from stimcirq import cirq_circuit_to_stim_circuit

stim_circuit = cirq_circuit_to_stim_circuit(noisy_circuit)
print(stim_circuit)
