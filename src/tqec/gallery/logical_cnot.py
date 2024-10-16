from tqec.computation.block_graph.graph import BlockGraph
from tqec.computation.zx_graph import ZXGraph
from tqec.position import Position3D


def logical_cnot_zx_graph(support_z_basis_observables: bool = True) -> ZXGraph:
    basis_str = "Z" if support_z_basis_observables else "X"
    cnot_zx = ZXGraph(f"Logical CNOT in {basis_str} basis")

    if support_z_basis_observables:
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


def logical_cnot_block_graph(support_z_basis_observables: bool = True) -> BlockGraph:
    logical_cnot_zx = logical_cnot_zx_graph(support_z_basis_observables)
    return logical_cnot_zx.to_block_graph(logical_cnot_zx.name)
