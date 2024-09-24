"""This is an example of compiling a logical CNOT `.dae` model to
`stim.Circuit`."""

from typing import Iterable
import stim
import sinter
import matplotlib.pyplot as plt

from tqec import (
    BlockGraph,
    compile_block_graph,
    annotate_detectors_automatically,
    ZXGraph,
    Position3D,
)
from tqec.noise_models import (
    AfterCliffordDepolarizingNoise,
    DepolarizingNoiseOnIdlingQubit,
)


if __name__ == "__main__":
    # 1.1 Import the `.dae` model as a `BlockGraph`
    block_graph = BlockGraph.from_dae_file("examples/assets/logical_cnot.dae")

    # 1.2 Or, create a `BlockGraph` from scratch
    # cnot_zx = ZXGraph("Logical CNOT ZX Graph")
    #
    # cnot_zx.add_z_node(Position3D(0, 0, 0))
    # cnot_zx.add_x_node(Position3D(0, 0, 1))
    # cnot_zx.add_z_node(Position3D(0, 0, 2))
    # cnot_zx.add_z_node(Position3D(0, 0, 3))
    # cnot_zx.add_x_node(Position3D(0, 1, 1))
    # cnot_zx.add_z_node(Position3D(0, 1, 2))
    # cnot_zx.add_z_node(Position3D(1, 1, 0))
    # cnot_zx.add_z_node(Position3D(1, 1, 1))
    # cnot_zx.add_z_node(Position3D(1, 1, 2))
    # cnot_zx.add_z_node(Position3D(1, 1, 3))
    #
    # cnot_zx.add_edge(Position3D(0, 0, 0), Position3D(0, 0, 1))
    # cnot_zx.add_edge(Position3D(0, 0, 1), Position3D(0, 0, 2))
    # cnot_zx.add_edge(Position3D(0, 0, 2), Position3D(0, 0, 3))
    # cnot_zx.add_edge(Position3D(0, 0, 1), Position3D(0, 1, 1))
    # cnot_zx.add_edge(Position3D(0, 1, 1), Position3D(0, 1, 2))
    # cnot_zx.add_edge(Position3D(0, 1, 2), Position3D(1, 1, 2))
    # cnot_zx.add_edge(Position3D(1, 1, 0), Position3D(1, 1, 1))
    # cnot_zx.add_edge(Position3D(1, 1, 1), Position3D(1, 1, 2))
    # cnot_zx.add_edge(Position3D(1, 1, 2), Position3D(1, 1, 3))
    # block_graph = cnot_zx.to_block_graph("Logical CNOT Block Graph")

    # 2. (Optional) Find and choose the logical observables
    observables = block_graph.get_abstract_observables()

    # 3. Compile the `BlockGraph` and generate noisy `stim.Circuit`
    # NOTE:that the scalable detector automation approach is still work in process.
    compiled_graph = compile_block_graph(block_graph)

    def generate_stim_circuit(k: int, p: float) -> stim.Circuit:
        circuit_without_detectors = compiled_graph.generate_stim_circuit(
            k,
            observables=[observables[1]],
            noise_models=[
                AfterCliffordDepolarizingNoise(p),
                DepolarizingNoiseOnIdlingQubit(p),
            ],
        )
        # For now, we annotate the detectors as post-processing step
        return annotate_detectors_automatically(circuit_without_detectors)

    # 4. Sampling and plot
    def gen_tasks() -> Iterable[sinter.Task]:
        for k in range(1, 4):  # d=3,5,7
            for p in [0.0005, 0.001, 0.004, 0.008, 0.01, 0.012, 0.014, 0.018]:
                yield sinter.Task(
                    circuit=generate_stim_circuit(k, p),
                    json_metadata={"d": 2 * k + 1, "r": 2 * k + 1, "p": p},
                )

    stats = sinter.collect(
        num_workers=16,
        tasks=gen_tasks(),
        max_errors=5000,
        max_shots=100_000_000,
        decoders=["pymatching"],
        print_progress=True,
    )
    fig, ax = plt.subplots()
    sinter.plot_error_rate(
        ax=ax,
        stats=stats,
        x_func=lambda stat: stat.json_metadata["p"],
        group_func=lambda stat: stat.json_metadata["d"],
    )
    ax.grid(axis="both")
    ax.legend()
    ax.loglog()
    ax.set_title("Logical CNOT Error Rate")
    fig.savefig("examples/assets/logical_cnot_result.png")
