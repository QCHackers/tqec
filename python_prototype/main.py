from tqec.display import display
from tqec.templates.scalable.square import ScalableAlternatingSquare
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
import cirq


def normalise_circuit(circuit: cirq.Circuit) -> cirq.Circuit:
    ordered_transformers = [
        merge_adjacent_resets,
        merge_adjacent_measurements,
        remove_mergeable_tag,
        cirq.synchronize_terminal_measurements,
        cirq.drop_empty_moments,
    ]
    for transformer in ordered_transformers:
        circuit = transformer(circuit)
    return circuit


template = ScalableQubitSquare(4)
plaquettes = [
    XXPlaquette(PlaquetteOrientation.UP),
    ZZPlaquette(PlaquetteOrientation.LEFT),
    XXXXPlaquette(),
    ZZZZPlaquette(),
    ZZPlaquette(PlaquetteOrientation.RIGHT),
    XXPlaquette(PlaquetteOrientation.DOWN),
]

display(template)
circuit = cirq.Circuit()
for layer_index in range(3):
    layer_circuit = generate_circuit(template, plaquettes, layer_index=layer_index)
    layer_circuit = normalise_circuit(layer_circuit)
    circuit += layer_circuit

print(circuit)

from stimcirq import cirq_circuit_to_stim_circuit

stim_circuit = cirq_circuit_to_stim_circuit(circuit)
print(stim_circuit)
