import argparse
from pathlib import Path

import stim

from tqec.circuit.detectors.construction import annotate_detectors_automatically
from tqec.compile.compile import CompiledGraph, compile_block_graph
from tqec.noise_models.after_clifford_depolarization import (
    AfterCliffordDepolarizingNoise,
)
from tqec.noise_models.idle_qubits import DepolarizingNoiseOnIdlingQubit
from tqec.position import Position3D
from tqec.sketchup.block_graph import BlockGraph
from tqec.sketchup.zx_graph import ZXGraph

BENCHMARK_FOLDER = Path(__file__).resolve().parent
TQEC_FOLDER = BENCHMARK_FOLDER.parent
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


def generate_stim_circuit(
    compiled_graph: CompiledGraph, k: int, p: float
) -> stim.Circuit:
    circuit_without_detectors = compiled_graph.generate_stim_circuit(
        k,
        noise_models=[
            AfterCliffordDepolarizingNoise(p),
            DepolarizingNoiseOnIdlingQubit(p),
        ],
    )
    # For now, we annotate the detectors as post-processing step
    return annotate_detectors_automatically(circuit_without_detectors)


def generate_cnot_circuits(*ks: int):
    # 1 Create `BlockGraph` representing the computation
    block_graph = create_block_graph(from_scratch=False)

    # 2. (Optional) Find and choose the logical observables
    observables = block_graph.get_abstract_observables()

    # 3. Compile the `BlockGraph`
    compiled_graph = compile_block_graph(
        block_graph,
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
