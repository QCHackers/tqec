import cirq
import matplotlib.pyplot as plt
import sinter
import stim
from stimcirq import cirq_circuit_to_stim_circuit

from tqec.constructions.qubit import ScalableQubitSquare
from tqec.detectors.gate import ObservableGate, RelativeMeasurement, ShiftCoordsGate
from tqec.detectors.transformer import fill_in_global_record_indices
from tqec.enums import PlaquetteOrientation
from tqec.generation.circuit import generate_circuit
from tqec.noise_models import (
    AfterCliffordDepolarizingNoise,
    AfterResetFlipNoise,
    BeforeMeasurementFlipNoise,
)
from tqec.plaquette.library import (
    XXXXPlaquette,
    ZZZZPlaquette,
)
from tqec.plaquette.library.xx import XXPlaquette
from tqec.plaquette.library.zz import ZZPlaquette
from tqec.position import Shape2D


def normalise_circuit(circuit: cirq.Circuit) -> cirq.Circuit:
    ordered_transformers = [
        cirq.drop_empty_moments,
    ]
    for transformer in ordered_transformers:
        circuit = transformer(circuit=circuit)
    return circuit


def to_noisy_circuit(circuit: cirq.Circuit, noise_level: float) -> cirq.Circuit:
    noise_models = [
        AfterCliffordDepolarizingNoise(noise_level),
        AfterResetFlipNoise(noise_level),
        BeforeMeasurementFlipNoise(noise_level),
    ]
    for nm in noise_models:
        circuit = circuit.with_noise(nm)
    return circuit


def generate_stim_circuit(
    dimension: int, noise_level: float, repetitions: int
) -> stim.Circuit:
    template = ScalableQubitSquare(dimension)
    plaquettes = [
        ZZPlaquette(PlaquetteOrientation.UP),
        XXPlaquette(
            PlaquetteOrientation.LEFT, include_initial_and_final_detectors=False
        ),
        ZZZZPlaquette(),
        XXXXPlaquette(include_initial_and_final_detectors=False),
        XXPlaquette(
            PlaquetteOrientation.RIGHT, include_initial_and_final_detectors=False
        ),
        ZZPlaquette(PlaquetteOrientation.DOWN),
    ]

    def make_repeated_layer(circuit: cirq.Circuit) -> cirq.Circuit:
        any_qubit = next(iter(circuit.all_qubits()), None)
        assert (
            any_qubit is not None
        ), "Could not find any qubit in the given Circuit instance."
        circuit_to_repeat = (
            cirq.Circuit([ShiftCoordsGate(0, 0, 1).on(any_qubit)]) + circuit
        )
        repeated_circuit_operation = cirq.CircuitOperation(
            circuit_to_repeat.freeze()
        ).repeat(repetitions)
        return cirq.Circuit([repeated_circuit_operation])

    layer_modificators = {1: make_repeated_layer}

    circuit = cirq.Circuit()
    for layer_index in range(3):
        layer_circuit = generate_circuit(template, plaquettes, layer_index=layer_index)
        layer_circuit = normalise_circuit(layer_circuit)
        circuit += layer_modificators.get(layer_index, lambda circ: circ)(layer_circuit)

    # Compute the qubits that should be measured to get the Z logical operator.
    plaquette_shape: Shape2D = plaquettes[0].shape
    assert all(
        p.shape == plaquette_shape for p in plaquettes
    ), "All plaquettes should have exactly the same shape for the moment."
    vertical_center_index: int = (1 + dimension // 2) * (plaquette_shape.y - 1)
    origin = cirq.GridQubit(vertical_center_index, plaquette_shape.x - 1)
    circuit.append(
        [
            ObservableGate(
                origin,
                [
                    RelativeMeasurement(
                        cirq.GridQubit(0, i * (plaquette_shape.x - 1)), -1
                    )
                    for i in range(dimension + 1)
                ],
            ).on(origin)
        ]
    )
    print(circuit)
    circuit_with_detectors = fill_in_global_record_indices(circuit)
    noisy_circuit = to_noisy_circuit(circuit_with_detectors, noise_level)

    return cirq_circuit_to_stim_circuit(noisy_circuit)


stim_circuit = generate_stim_circuit(2, 0.001, 0)

surface_code_tasks = [
    sinter.Task(
        circuit=generate_stim_circuit(d - 1, noise, 3 * d),
        json_metadata={"d": d, "r": 3 * d, "p": noise},
    )
    for d in [3]
    for noise in [0.001, 0.002, 0.004]
]

collected_surface_code_stats: list[sinter.TaskStats] = sinter.collect(
    num_workers=20,
    tasks=surface_code_tasks,
    decoders=["pymatching"],
    max_shots=100_000,
    max_errors=5_000,
    print_progress=False,
)

fig, ax = plt.subplots(1, 1)
sinter.plot_error_rate(
    ax=ax,
    stats=collected_surface_code_stats,
    x_func=lambda stat: stat.json_metadata["p"],
    group_func=lambda stat: stat.json_metadata["d"],
    failure_units_per_shot_func=lambda stat: stat.json_metadata["r"],
)
ax.loglog()
ax.set_title("Surface Code Error Rates per Round under Circuit Noise")
ax.set_xlabel("Phyical Error Rate")
ax.set_ylabel("Logical Error Rate per Round")
ax.grid(which="major")
ax.grid(which="minor")
ax.legend()
fig.set_dpi(120)  # Show it bigger
