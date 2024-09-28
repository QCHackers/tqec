from collections import defaultdict
from dataclasses import dataclass
from typing import Literal, Protocol
from copy import deepcopy

import cirq

from tqec.compile.block import CompiledBlock
from tqec.compile.specs import CubeSpec
from tqec.exceptions import TQECException
from tqec.plaquette.enums import PlaquetteSide
from tqec.plaquette.library.pauli import MeasurementBasis, ResetBasis
from tqec.plaquette.plaquette import Plaquette
from tqec.position import Direction3D
from tqec.sketchup.block_graph import PipeType


@dataclass(frozen=True)
class SubstitutionKey:
    """The key for selecting the substitution rule.

    Substitution rules will be selected based on the key to apply the substitution
    during the block graph compilation.

    Attributes:
        spec1: the cube specification of the first cube. By convention, the cube
            corresponding to `spec1` should have a smaller position than the cube
            corresponding to `spec2`.
        spec2: the cube specification of the second cube.
        pipe_type: the type of the pipe connecting the two cubes.
    """

    spec1: CubeSpec
    spec2: CubeSpec
    pipe_type: PipeType


class SubstitutionRule(Protocol):
    """Protocol for applying the substitution to the two blocks connected by a
    pipe, based on the `SubstitutionKey`.

    Users can define their own rules for the substitution by
    implementing this protocol and register the rules during
    compilation.
    """

    def __call__(
        self,
        key: SubstitutionKey,
        block1: CompiledBlock,
        block2: CompiledBlock,
    ) -> tuple[CompiledBlock, CompiledBlock]:
        """Substitute the two blocks with the given key.

        Args:
            key: `SubstitutionKey` that includes the necessary information for the
                substitution, including the cube specifications and the pipe type that
                is connecting the two blocks.
            block1: the first block to substitute.
            block2: the second block to substitute.
        """
        ...


def default_substitution_rule(
    key: SubstitutionKey,
    block1: CompiledBlock,
    block2: CompiledBlock,
) -> tuple[CompiledBlock, CompiledBlock]:
    """The default substitution rule for the block graph compilation."""
    # 1. The spatial junctions are not supported yet
    if key.spec1.is_spatial_junction or key.spec2.is_spatial_junction:
        raise TQECException("Spatial junctions are not supported yet.")
    # 2. Substitute the time-direction pipe
    if key.pipe_type.direction == Direction3D.Z:
        return _substitute_in_time_direction(key, block1, block2)
    # 3. Substitute the space-direction pipe
    else:
        return _substitute_in_space_with_usual_cubes(key, block1, block2)


DEFAULT_SUBSTITUTION_RULES: defaultdict[SubstitutionKey, SubstitutionRule] = (
    defaultdict(lambda: default_substitution_rule)
)


def _substitute_in_time_direction(
    key: SubstitutionKey,
    block1: CompiledBlock,
    block2: CompiledBlock,
) -> tuple[CompiledBlock, CompiledBlock]:
    assert key.pipe_type.direction == Direction3D.Z, "Pipe direction must be Z."
    # Substitute the final layer of the bottom block with the bulk layer
    bottom_block = block1.with_updated_layer(
        plaquettes_to_update=deepcopy(block1.layers[1].collection),
        layer_to_update=block1.num_layers - 1,
    )
    # Substitute the first layer of the top block with the bulk layer
    top_block = block2.with_updated_layer(
        plaquettes_to_update=deepcopy(block2.layers[1].collection),
        layer_to_update=0,
    )
    # If the pipe has a hadamard, apply the hadamard transformation
    # The hadamard transformation is applied to the end of the bottom block
    if key.pipe_type.has_hadamard:
        raise TQECException("Pipe with hadamard is not supported yet.")
    return bottom_block, top_block


def _substitute_in_space_with_usual_cubes(
    key: SubstitutionKey,
    block1: CompiledBlock,
    block2: CompiledBlock,
) -> tuple[CompiledBlock, CompiledBlock]:
    pipe_type = key.pipe_type
    assert (
        not key.spec1.is_spatial_junction and not key.spec2.is_spatial_junction
    ), "Both cubes must not be spatial junction."
    assert pipe_type.direction != Direction3D.Z, "Pipe direction must be X or Y."
    if pipe_type.has_hadamard:
        raise TQECException("Pipe with hadamard is not supported yet.")
    substitute_side1 = (
        PlaquetteSide.RIGHT
        if pipe_type.direction == Direction3D.X
        else PlaquetteSide.DOWN
    )
    substitute_side2 = substitute_side1.opposite()
    # Get reset/mesurement basis
    basis = pipe_type.temporal_basis()
    block1 = _substitute_on_the_border(block1, substitute_side1, basis)
    block2 = _substitute_on_the_border(block2, substitute_side2, basis)
    return block1, block2


def _substitute_on_the_border(
    block: CompiledBlock,
    plaquette_side: PlaquetteSide,
    basis: Literal["X", "Z"],
) -> CompiledBlock:
    if plaquette_side == PlaquetteSide.LEFT:
        substitution = {1: 6, 8: 9, 7: 10}
    elif plaquette_side == PlaquetteSide.UP:
        substitution = {2: 12, 5: 10, 6: 9}
    elif plaquette_side == PlaquetteSide.DOWN:
        substitution = {3: 7, 14: 10, 13: 9}
    else:  # plaquette_side == PlaquetteSide.RIGHT:
        substitution = {4: 13, 11: 9, 12: 10}
    # 1. Fill in/Substitue the plaquettes on the border
    for i in range(block.num_layers):
        block = block.with_updated_layer(
            plaquettes_to_update={
                dst: deepcopy(block.layers[i][src]) for dst, src in substitution.items()
            },
            layer_to_update=i,
        )
    # 2. Add resets/measurements on the middle of the border
    for i in substitution.keys():
        _inplace_add_operation_on_data_qubits(
            block.layers[0][i], plaquette_side, ResetBasis(basis), 1
        )
        _inplace_add_operation_on_data_qubits(
            block.layers[-1][i], plaquette_side, MeasurementBasis(basis), -1
        )
    return block


def _inplace_add_operation_on_data_qubits(
    plaquette: Plaquette,
    side: PlaquetteSide,
    operation_basis: ResetBasis | MeasurementBasis,
    moment_schedule: int,
) -> None:
    qubits = plaquette.qubits.get_qubits_on_side(side)
    # Do not add resets on qubits that have already be reset
    moment = plaquette.circuit.moment_at_schedule(moment_schedule)
    operation_to_add = []
    for q in qubits:
        gq = q.to_grid_qubit()
        if moment.operates_on([gq]):
            continue
        operation_to_add.append(operation_basis(gq))
    plaquette.circuit.add_to_schedule_index(
        moment_schedule, cirq.Moment(*operation_to_add)
    )
