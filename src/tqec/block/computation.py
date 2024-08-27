from __future__ import annotations

import typing
from functools import partial

import cirq
import cirq.circuits
import networkx as nx
from tqec.block.block import ComputationBlock
from tqec.block.library import cube_to_block, pipe_to_block
from tqec.circuit.schedule import ScheduledCircuit, merge_scheduled_circuits
from tqec.exceptions import TQECException
from tqec.position import Position3D
from tqec.sketchup import BlockGraph, Pipe
from tqec.templates.scale import LinearFunction


_COMPUTATION_DATA_KEY = "tqec_computation_block"


class Computation:
    """Represents a topological quantum error corrected computation.

    The computation is represented by a mapping from a position to the
    computational block whose origin is located at that position.
    """

    def __init__(
        self,
        blocks: typing.Mapping[Position3D, ComputationBlock],
    ) -> None:
        self._graph: nx.Graph = nx.Graph()
        self.blocks = blocks
        for position, block in blocks.items():
            self._graph.add_node(position, **{_COMPUTATION_DATA_KEY: block})

    @staticmethod
    def from_block_graph(graph: BlockGraph, dimension: LinearFunction) -> Computation:
        blocks = {}
        for cube in graph.cubes:
            blocks[cube.position] = cube_to_block(cube, dimension)
        for pipe in graph.pipes:
            # TODO: ensure blocks connected by pipes are compatible
            # TODO: pipes get a size now -> make sure everything is shifted correctly
            position = _get_pipe_position(pipe)

            blocks[position] = pipe_to_block(pipe, dimension)
        return Computation(blocks)

    def to_circuit(self) -> cirq.Circuit:
        """Build and return the quantum circuit representing the computation.

        Raises:
            TQECException: if any of the circuits obtained by instantiating the
                computational blocks is contains a qubit that is not a cirq.GridQubit.

        Returns:
            a cirq.Circuit instance representing the full computation.
        """
        instantiated_scheduled_blocks: list[ScheduledCircuit] = []
        depth = 0
        for position, block in self.blocks.items():
            spatially_shifted_circuit = block.instantiate().transform_qubits(
                partial(_shift_qubits, position)
            )
            instantiated_scheduled_blocks.append(
                ScheduledCircuit(spatially_shifted_circuit, depth)
            )
            depth += block.depth

        return merge_scheduled_circuits(instantiated_scheduled_blocks)


def _get_pipe_position(pipe: Pipe) -> Position3D:
    return pipe.u.position


def _shift_qubits(position: Position3D, q: cirq.Qid) -> cirq.GridQubit:
    if not isinstance(q, cirq.GridQubit):
        raise TQECException(
            f"Found a circuit with {q} that is not a cirq.GridQubit instance."
        )
    return q + (position.x, position.y)
