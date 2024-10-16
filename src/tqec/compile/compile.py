from dataclasses import dataclass
from typing import Literal
import warnings

import stim

from tqec.circuit.schedule import ScheduledCircuit
from tqec.compile.block import BlockLayout, CompiledBlock
from tqec.compile.observables import inplace_add_observables
from tqec.compile.specs.base import (
    BlockBuilder,
    CubeSpec,
    PipeSpec,
    SubstitutionBuilder,
)
from tqec.compile.specs.library.css import CSS_BLOCK_BUILDER, CSS_SUBSTITUTION_BUILDER
from tqec.computation.block_graph import AbstractObservable, BlockGraph
from tqec.exceptions import TQECException, TQECWarning
from tqec.noise_models import NoiseModel
from tqec.plaquette.plaquette import RepeatedPlaquettes
from tqec.position import Direction3D, Displacement, Position3D
from tqec.scale import round_or_fail


@dataclass
class CompiledGraph:
    """Represents a compiled block graph.

    This class should be easy to scale and generate circuits directly.

    Attributes:
        layout_slices: a list of `BlockLayout` objects that represent the compiled blocks
            at contiguous time slices.
        observables: a list of `AbstractObservable` objects that represent the observables
            to be included in the compiled circuit.
    """

    layout_slices: list[BlockLayout]
    observables: list[AbstractObservable]

    def __post_init__(self) -> None:
        if len(self.layout_slices) == 0:
            raise TQECException(
                "The compiled graph should have at least one time slice "
                "but got an empty layout_slices."
            )
        # Use warning instead of exception because a qec circuit without observable
        # may still be useful, e.g. do statistics on the detection events.
        if len(self.observables) == 0:
            warnings.warn("The compiled graph includes no observable.", TQECWarning)

    def generate_stim_circuit(
        self,
        k: int,
        noise_model: NoiseModel | None = None,
    ) -> stim.Circuit:
        """Generate the stim circuit from the compiled graph.

        Args:
            k: The scale factor of the templates.
            noise_models: The noise models to be applied to the circuit.

            A compiled stim circuit.
        """
        # assemble circuits time slice by time slice, layer by layer.
        circuits: list[list[ScheduledCircuit]] = []
        for layout in self.layout_slices:
            circuits.append(
                [layout.instantiate_layer(i, k) for i in range(layout.num_layers)]
            )
        # construct observables
        inplace_add_observables(
            circuits,
            [layout.template for layout in self.layout_slices],
            self.observables,
            k,
        )
        # shift and merge circuits
        circuit = self._shift_and_merge_circuits(circuits, k)
        # apply noise models
        if noise_model is not None:
            circuit = noise_model.noisy_circuit(circuit)
        return circuit

    def _shift_and_merge_circuits(
        self, circuits: list[list[ScheduledCircuit]], k: int
    ) -> stim.Circuit:
        """

        Warning:
            Modify in-place the provided `circuits`.

        Args:
            circuits:

        Returns:

        """
        # First, shift all the circuits to make sure that they are each applied
        # on the correct qubits
        self._shift_all_circuits_inplace(circuits, k)
        # Then, get a global qubit index map to remap the circuit indices on the
        # fly.
        needed_qubits = frozenset.union(
            *[c.qubits for clayer in circuits for c in clayer]
        )
        global_q2i = {q: i for i, q in enumerate(sorted(needed_qubits))}
        # Add the QUBIT_COORDS instructions at the beginning of the circuit
        final_circuit = stim.Circuit()
        for q, i in global_q2i.items():
            final_circuit.append(q.to_qubit_coords_instruction(i))
        # Merge all the circuits, constructing a REPEAT block when needed.
        for t, layout in enumerate(self.layout_slices):
            for i in range(layout.num_layers):
                # Remap the circuit qubit indices to be sure that there will be
                # no index clash.
                circuit = circuits[t][i]
                local_indices_to_global_indices = {
                    local_index: global_q2i[q]
                    for local_index, q in circuit.qubit_map.items()
                }
                circuit.map_qubit_indices(local_indices_to_global_indices, inplace=True)

                # Append either the full circuit or a REPEAT block.
                layer = layout.layers[i]
                if isinstance(layer, RepeatedPlaquettes):
                    final_circuit += circuits[t][i].get_repeated_circuit(
                        round_or_fail(layer.repetitions(k)),
                        include_qubit_coords=False,
                    )
                else:
                    final_circuit += circuits[t][i].get_circuit(
                        include_qubit_coords=False
                    )
                # Do not forget to append a TICK here
                final_circuit.append("TICK", [], [])
        # We appended one extra TICK at the end, remove it and return the result.
        return final_circuit[:-1]

    def _shift_all_circuits_inplace(
        self, circuits: list[list[ScheduledCircuit]], k: int
    ) -> None:
        for t, layout in enumerate(self.layout_slices):
            # We need to shift the circuit based on the shift of the layout template.
            origin_shift = layout.template.origin_shift
            element_shape = layout.template.element_shape(k)
            increment = layout.template.get_increments()
            for i in range(layout.num_layers):
                qubit_map = {
                    q: q
                    + Displacement(
                        origin_shift.x * element_shape.x * increment.x,
                        origin_shift.y * element_shape.y * increment.y,
                    )
                    for q in circuits[t][i].qubits
                }
                circuits[t][i].map_to_qubits(qubit_map, inplace=True)


def compile_block_graph(
    block_graph: BlockGraph,
    block_builder: BlockBuilder = CSS_BLOCK_BUILDER,
    substitution_builder: SubstitutionBuilder = CSS_SUBSTITUTION_BUILDER,
    observables: list[AbstractObservable] | Literal["auto"] | None = "auto",
) -> CompiledGraph:
    """Compile a block graph.

    Args:
        block_graph: The block graph to compile.
        block_builder: A callable that specifies how to build the `CompiledBlock` from
            the specified `CubeSpecs`. Defaults to the block builder for the css type
            surface code.
        substitution_builder: A callable that specifies how to build the substitution
            plaquettes from the specified `PipeSpec`. Defaults to the substitution
            builder for the css type surface code.
        observables: The abstract observables to be included in the compiled
            circuit.
            If set to "auto", the observables will be automatically determined from
            the block graph. If a list of abstract observables is provided, only
            those observables will be included in the compiled circuit. If set to
            None, no observables will be included in the compiled circuit.

    Returns:
        A `CompiledGraph` object that can be used to generate a cirq/stim circuit and
        scale easily.
    """
    if block_graph.num_open_ports != 0:
        raise TQECException(
            "Can not compile a block graph with open ports into circuits."
        )
    cube_specs = {
        cube: CubeSpec.from_cube(cube, block_graph) for cube in block_graph.cubes
    }

    # 0. Set the minimum z of block graph to 0.(time starts from zero)
    block_graph = block_graph.with_zero_min_z()

    # 1. Get the base compiled blocks before applying the substitution rules.
    blocks: dict[Position3D, CompiledBlock] = {}
    for cube in block_graph.cubes:
        spec = cube_specs[cube]
        blocks[cube.position] = block_builder(spec)

    # 2. Apply the substitution rules to the compiled blocks inplace.
    pipes = block_graph.pipes
    time_pipes = [pipe for pipe in pipes if pipe.pipe_type.direction == Direction3D.Z]
    space_pipes = [pipe for pipe in pipes if pipe.pipe_type.direction != Direction3D.Z]
    # Note that the order of the pipes to apply the substitution rules is important.
    # To keep the time-direction substitution rules from removing the extra resets
    # added by the space-direction substitution rules, we first apply the time-direction
    # substitution rules.
    for pipe in time_pipes + space_pipes:
        pos1, pos2 = pipe.u.position, pipe.v.position
        key = PipeSpec(cube_specs[pipe.u], cube_specs[pipe.v], pipe.pipe_type)
        substitution = substitution_builder(key)
        blocks[pos1].update_layers(substitution.src)
        blocks[pos2].update_layers(substitution.dst)

    # 3. Collect by time and create the blocks layout.
    min_z = min(pos.z for pos in blocks.keys())
    max_z = max(pos.z for pos in blocks.keys())
    layout_slices: list[BlockLayout] = [
        BlockLayout({pos.as_2d(): block for pos, block in blocks.items() if pos.z == z})
        for z in range(min_z, max_z + 1)
    ]

    # 4. Get the abstract observables to be included in the compiled circuit.
    obs_included: list[AbstractObservable]
    if observables is None:
        obs_included = []
    elif observables == "auto":
        obs_included, _ = block_graph.get_abstract_observables()
    else:
        obs_included = observables

    return CompiledGraph(layout_slices, obs_included)
