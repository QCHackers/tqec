"""This is an example of compiling a logical CNOT `.dae` model to
`stim.Circuit`."""

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import sinter

from tqec import (
    BlockGraph,
    Position3D,
    ZXGraph,
    compile_block_graph,
)
from tqec.noise_models import NoiseModel
from tqec.simulation.generation import generate_stim_circuits_with_detectors
from tqec.simulation.plotting.inset import plot_observable_as_inset

EXAMPLE_FOLDER = Path(__file__).parent
TQEC_FOLDER = EXAMPLE_FOLDER.parent
ASSETS_FOLDER = TQEC_FOLDER / "assets"
CNOT_DAE_FILE = ASSETS_FOLDER / "logical_cnot.dae"


def create_block_graph(from_scratch: bool = False) -> BlockGraph:
    if not from_scratch:
        return BlockGraph.from_dae_file(CNOT_DAE_FILE)

    cnot_zx = ZXGraph("Logical CNOT ZX Graph")

    cnot_zx.add_z_node(Position3D(0, 0, 0))
    cnot_zx.add_x_node(Position3D(0, 0, 1))
    cnot_zx.add_z_node(Position3D(0, 0, 2))
    cnot_zx.add_z_node(Position3D(0, 0, 3))
    cnot_zx.add_x_node(Position3D(0, 1, 1))
    cnot_zx.add_z_node(Position3D(0, 1, 2))
    cnot_zx.add_z_node(Position3D(1, 1, 0))
    cnot_zx.add_z_node(Position3D(1, 1, 1))
    cnot_zx.add_z_node(Position3D(1, 1, 2))
    cnot_zx.add_z_node(Position3D(1, 1, 3))

    cnot_zx.add_edge(Position3D(0, 0, 0), Position3D(0, 0, 1))
    cnot_zx.add_edge(Position3D(0, 0, 1), Position3D(0, 0, 2))
    cnot_zx.add_edge(Position3D(0, 0, 2), Position3D(0, 0, 3))
    cnot_zx.add_edge(Position3D(0, 0, 1), Position3D(0, 1, 1))
    cnot_zx.add_edge(Position3D(0, 1, 1), Position3D(0, 1, 2))
    cnot_zx.add_edge(Position3D(0, 1, 2), Position3D(1, 1, 2))
    cnot_zx.add_edge(Position3D(1, 1, 0), Position3D(1, 1, 1))
    cnot_zx.add_edge(Position3D(1, 1, 1), Position3D(1, 1, 2))
    cnot_zx.add_edge(Position3D(1, 1, 2), Position3D(1, 1, 3))
    return cnot_zx.to_block_graph("Logical CNOT Block Graph")


def main() -> None:
    # 1 Create `BlockGraph` representing the computation
    block_graph = create_block_graph(from_scratch=False)
    zx_graph = block_graph.to_zx_graph("Logical CNOT")
    correlation_surfaces = zx_graph.find_correlation_subgraphs()

    # 2. (Optional) Find and choose the logical observables
    observables = block_graph.get_abstract_observables()
    _OBSERVABLE_ID: int = 2

    # 3. Compile the `BlockGraph`
    # NOTE:that the scalable detector automation approach is still work in process.
    compiled_graph = compile_block_graph(
        block_graph,
        observables=[observables[_OBSERVABLE_ID]],
    )

    # 4. Generate `stim.Circuit`s from the compiled graph and run the simulation
    def gen_tasks() -> Iterable[sinter.Task]:
        yield from (
            sinter.Task(
                circuit=circuit,
                json_metadata={"d": 2 * k + 1, "r": 2 * k + 1, "p": p},
            )
            for circuit, k, p in generate_stim_circuits_with_detectors(
                compiled_graph,
                range(1, 5),
                [0.0005, 0.001, 0.004, 0.008, 0.01, 0.012, 0.014, 0.018],
                NoiseModel.uniform_depolarizing,
            )
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
    plot_observable_as_inset(ax, zx_graph, correlation_surfaces[_OBSERVABLE_ID])
    ax.grid(axis="both")
    ax.legend()
    ax.loglog()
    ax.set_title("Logical CNOT Error Rate")
    fig.savefig(ASSETS_FOLDER / f"logical_cnot_result_observable_{_OBSERVABLE_ID}.png")


if __name__ == "__main__":
    main()
