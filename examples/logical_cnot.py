"""This is an example of compiling a logical CNOT `.dae` model to
`stim.Circuit`."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy
import sinter

from tqec import Position3D, ZXGraph
from tqec.compile.specs.library.css import CSS_SPEC_RULES
from tqec.noise_models import NoiseModel
from tqec.simulation.plotting.inset import plot_observable_as_inset
from tqec.simulation.simulation import start_simulation_using_sinter

EXAMPLE_FOLDER = Path(__file__).parent
TQEC_FOLDER = EXAMPLE_FOLDER.parent
ASSETS_FOLDER = TQEC_FOLDER / "assets"


def create_zx_graph(z_basis: bool = True) -> ZXGraph:
    basis_str = "Z" if z_basis else "X"
    cnot_zx = ZXGraph(f"Logical CNOT in {basis_str} basis")

    if z_basis:
        cnot_zx.add_z_node(Position3D(0, 0, 0))
        cnot_zx.add_z_node(Position3D(1, 1, 0))
        cnot_zx.add_z_node(Position3D(0, 0, 3))
        cnot_zx.add_z_node(Position3D(1, 1, 3))
    else:
        cnot_zx.add_x_node(Position3D(0, 0, 0))
        cnot_zx.add_x_node(Position3D(1, 1, 0))
        cnot_zx.add_x_node(Position3D(0, 0, 3))
        cnot_zx.add_x_node(Position3D(1, 1, 3))

    cnot_zx.add_x_node(Position3D(0, 0, 1))
    cnot_zx.add_z_node(Position3D(0, 0, 2))
    cnot_zx.add_x_node(Position3D(0, 1, 1))
    cnot_zx.add_z_node(Position3D(0, 1, 2))
    cnot_zx.add_z_node(Position3D(1, 1, 1))
    cnot_zx.add_z_node(Position3D(1, 1, 2))

    cnot_zx.add_edge(Position3D(0, 0, 0), Position3D(0, 0, 1))
    cnot_zx.add_edge(Position3D(0, 0, 1), Position3D(0, 0, 2))
    cnot_zx.add_edge(Position3D(0, 0, 2), Position3D(0, 0, 3))
    cnot_zx.add_edge(Position3D(0, 0, 1), Position3D(0, 1, 1))
    cnot_zx.add_edge(Position3D(0, 1, 1), Position3D(0, 1, 2))
    cnot_zx.add_edge(Position3D(0, 1, 2), Position3D(1, 1, 2))
    cnot_zx.add_edge(Position3D(1, 1, 0), Position3D(1, 1, 1))
    cnot_zx.add_edge(Position3D(1, 1, 1), Position3D(1, 1, 2))
    cnot_zx.add_edge(Position3D(1, 1, 2), Position3D(1, 1, 3))
    return cnot_zx


def generate_graphs(z_basis: bool) -> None:
    # 1 Create `BlockGraph` representing the computation
    zx_graph = create_zx_graph(z_basis=z_basis)
    block_graph = zx_graph.to_block_graph()
    correlation_surfaces = zx_graph.find_correlation_subgraphs()

    # 2. Find and choose the logical observables
    observables = block_graph.get_abstract_observables()
    # Optional: filter observables here
    # observables = [observables[0]]

    stats = start_simulation_using_sinter(
        block_graph,
        range(1, 5),
        list(numpy.logspace(-5, -1, 10)),
        NoiseModel.uniform_depolarizing,
        cube_specifications=CSS_SPEC_RULES,
        observables=observables,
        num_workers=16,
        max_shots=100_000_000,
        max_errors=5_000,
        decoders=["pymatching"],
        print_progress=True,
    )

    for i, stat in enumerate(stats):
        fig, ax = plt.subplots()
        sinter.plot_error_rate(
            ax=ax,
            stats=stat,
            x_func=lambda stat: stat.json_metadata["p"],
            group_func=lambda stat: stat.json_metadata["d"],
        )
        plot_observable_as_inset(ax, zx_graph, correlation_surfaces[i])
        ax.grid(axis="both")
        ax.legend()
        ax.loglog()
        ax.set_title("Logical CNOT Error Rate")
        basis_str = "Z" if z_basis else "X"
        fig.savefig(
            ASSETS_FOLDER / f"logical_cnot_result_{basis_str}_observable_{i}.png"
        )


def main():
    generate_graphs(True)
    generate_graphs(False)


if __name__ == "__main__":
    main()
