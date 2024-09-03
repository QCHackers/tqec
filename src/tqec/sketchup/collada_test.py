import os
import tempfile

import pytest

from tqec.sketchup.zx_graph import ZXGraph, Position3D, NodeType
from tqec.sketchup.block_graph import BlockGraph


@pytest.mark.parametrize("pipe_length", [0.5, 1.0, 2.0, 10.0])
def test_logical_cnot_collada_write_read(pipe_length: float) -> None:
    zx_graph = ZXGraph("Logical CNOT ZX Graph")
    for position, node_type in [
        (Position3D(0, 0, 0), NodeType.Z),
        (Position3D(0, 0, 1), NodeType.X),
        (Position3D(0, 0, 2), NodeType.Z),
        (Position3D(0, 0, 3), NodeType.Z),
        (Position3D(0, 1, 1), NodeType.X),
        (Position3D(0, 1, 2), NodeType.Z),
        (Position3D(1, 1, 0), NodeType.Z),
        (Position3D(1, 1, 1), NodeType.Z),
        (Position3D(1, 1, 2), NodeType.Z),
        (Position3D(1, 1, 3), NodeType.Z),
    ]:
        zx_graph.add_node(position, node_type)

    for u, v in [
        (Position3D(0, 0, 0), Position3D(0, 0, 1)),
        (Position3D(0, 0, 1), Position3D(0, 0, 2)),
        (Position3D(0, 0, 2), Position3D(0, 0, 3)),
        (Position3D(0, 0, 1), Position3D(0, 1, 1)),
        (Position3D(0, 1, 1), Position3D(0, 1, 2)),
        (Position3D(0, 1, 2), Position3D(1, 1, 2)),
        (Position3D(1, 1, 0), Position3D(1, 1, 1)),
        (Position3D(1, 1, 1), Position3D(1, 1, 2)),
        (Position3D(1, 1, 2), Position3D(1, 1, 3)),
    ]:
        zx_graph.add_edge(u, v)

    block_graph = zx_graph.to_block_graph()

    # Set `delete=False` to be compatible with Windows
    # https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile
    with tempfile.NamedTemporaryFile(suffix=".dae", delete=False) as temp_file:
        block_graph.to_dae_file(temp_file.name, pipe_length)
        block_graph_from_file = BlockGraph.from_dae_file(
            temp_file.name, "Logical CNOT Block Graph"
        )
        assert block_graph_from_file == block_graph
        assert block_graph_from_file.to_zx_graph() == zx_graph

    # Manually delete the temporary file
    os.remove(temp_file.name)
