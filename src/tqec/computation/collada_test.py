import os
import tempfile

import pytest

from tqec.computation.block_graph import BlockGraph
from tqec.gallery.logical_cnot import logical_cnot_block_graph, logical_cnot_zx_graph


@pytest.mark.parametrize("pipe_length", [0.5, 1.0, 2.0, 10.0])
def test_logical_cnot_collada_write_read(pipe_length: float) -> None:
    block_graph = logical_cnot_block_graph("open")

    # Set `delete=False` to be compatible with Windows
    # https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile
    with tempfile.NamedTemporaryFile(suffix=".dae", delete=False) as temp_file:
        block_graph.to_dae_file(temp_file.name, pipe_length)
        block_graph_from_file = BlockGraph.from_dae_file(
            temp_file.name, "Logical CNOT Block Graph"
        )
        assert block_graph_from_file == block_graph
        assert block_graph_from_file.to_zx_graph() == logical_cnot_zx_graph("open")

    # Manually delete the temporary file
    os.remove(temp_file.name)
