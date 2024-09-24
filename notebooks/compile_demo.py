from matplotlib.pyplot import annotate
from tqec import BlockGraph, CubeType, Position3D, PipeType
from tqec.circuit import annotate_detectors_automatically
from tqec.compile import compile_block_graph

# 1. Logical Memory(1 Cube)
# idle = BlockGraph("Single Cube Idle")
# idle.add_cube(Position3D(0, 0, 0), CubeType.XZX)
# circuit = compile_block_graph_to_stim(idle, k=1)
# print(circuit)

# 2. Logical Memory(2 Cubes)
# idle_2cube = BlockGraph("Two Cubes Idle")
# idle_2cube.add_cube(Position3D(0, 0, 0), CubeType.ZXZ)
# idle_2cube.add_cube(Position3D(0, 0, 1), CubeType.ZXZ)
# idle_2cube.add_pipe(Position3D(0, 0, 0), Position3D(0, 0, 1), PipeType.ZXO)
# circuit = compile_block_graph_to_stim(idle_2cube, k=1)
# print(circuit)

# 3. Merge and split
# merge = BlockGraph("Merge and Split")
# merge.add_cube(Position3D(0, 0, 0), CubeType.XZZ)
# merge.add_cube(Position3D(0, 1, 0), CubeType.XZZ)
# merge.add_pipe(Position3D(0, 0, 0), Position3D(0, 1, 0), PipeType.XOZ)
# circuit = compile_block_graph_to_stim(merge, k=1)
# print(circuit)


# 4. L-shape
# lshape = BlockGraph("L shape")
# lshape.add_cube(Position3D(0, 0, 0), CubeType.XZX)
# lshape.add_cube(Position3D(1, 0, 0), CubeType.XZX)
# lshape.add_cube(Position3D(0, 0, 1), CubeType.XZX)
# lshape.add_pipe(Position3D(0, 0, 0), Position3D(1, 0, 0), PipeType.OZX)
# lshape.add_pipe(Position3D(0, 0, 0), Position3D(0, 0, 1), PipeType.XZO)
# circuit = compile_block_graph_to_stim(lshape, k=1)
# print(circuit)


# 5. CNOT
cnot = BlockGraph.from_dae_file("notebooks/assets/clean_exportable_cnot.dae")
compiled_graph = compile_block_graph(cnot)
circuit_without_detectors = compiled_graph.generate_stim_circuit(k=1)
circuit = annotate_detectors_automatically(circuit_without_detectors)
print(circuit)
