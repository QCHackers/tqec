import argparse
from pathlib import Path

import stim

from tqec.circuit.detectors.construction import annotate_detectors_automatically
from tqec.compile.compile import CompiledGraph, compile_block_graph
from tqec.compile.specs.library.css import CSS_BLOCK_BUILDER, CSS_SUBSTITUTION_BUILDER
from tqec.computation.zx_graph import ZXGraph
from tqec.noise_models import NoiseModel
from tqec.position import Position3D

BENCHMARK_FOLDER = Path(__file__).resolve().parent
TQEC_FOLDER = BENCHMARK_FOLDER.parent
ASSETS_FOLDER = TQEC_FOLDER / "assets"
CNOT_DAE_FILE = ASSETS_FOLDER / "logical_cnot.dae"


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


def generate_stim_circuit(
    compiled_graph: CompiledGraph, k: int, p: float
) -> stim.Circuit:
    circuit_without_detectors = compiled_graph.generate_stim_circuit(
        k, noise_model=NoiseModel.uniform_depolarizing(p)
    )
    # For now, we annotate the detectors as post-processing step
    return annotate_detectors_automatically(circuit_without_detectors)


def generate_cnot_circuits(*ks: int):
    # 1 Create `BlockGraph` representing the computation
    zx_graph = create_zx_graph(True)
    block_graph = zx_graph.to_block_graph()

    # 2. (Optional) Find and choose the logical observables
    observables, _ = block_graph.get_abstract_observables()

    # 3. Compile the `BlockGraph`
    compiled_graph = compile_block_graph(
        block_graph,
        block_builder=CSS_BLOCK_BUILDER,
        substitution_builder=CSS_SUBSTITUTION_BUILDER,
        observables=[observables[1]],
    )

    for k in ks:
        _ = generate_stim_circuit(compiled_graph, k, 0.001)


def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "-k",
        help="The scale factors applied to the circuits.",
        nargs="+",
        type=int,
        required=True,
    )
    args = parser.parse_args()
    generate_cnot_circuits(*args.k)


if __name__ == "__main__":
    main()
