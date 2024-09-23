from typing import Literal
import cirq
import stim
import stimcirq

from tqec.circuit.operations.measurement import Measurement
from tqec.circuit.operations.operation import make_observable
from tqec.circuit.operations.transformer import transform_to_stimcirq_compatible
from tqec.circuit.schedule import ScheduledCircuit, merge_scheduled_circuits
from tqec.compile.observables import (
    get_center_qubit_at_horizontal_pipe,
    get_midline_qubits_for_cube,
    get_stabilizer_region_qubits_for_pipe,
)
from tqec.compile.substitute import (
    SubstitutionKey,
    SubstitutionRule,
    DEFAULT_SUBSTITUTION_RULES,
)
from tqec.exceptions import TQECException, TQECWarning
from tqec.plaquette.plaquette import RepeatedPlaquettes
from tqec.position import Direction3D, Position3D
from tqec.sketchup.block_graph import AbstractObservable, BlockGraph, Cube
from tqec.compile.block import CompiledBlock, map_qubit_at_block
from tqec.compile.specs import DEFAULT_SPEC_RULES, CubeSpec, SpecRule


def compile_block_graph_to_stim(
    block_graph: BlockGraph,
    k: int,
    observables: list[AbstractObservable] | Literal["auto"] | None = "auto",
    custom_spec_rules: dict[CubeSpec, SpecRule] | None = None,
    custom_substitute_rules: dict[SubstitutionKey, SubstitutionRule] | None = None,
) -> stim.Circuit:
    """Compile a block graph into a stim circuit.

    Args:
        block_graph: The block graph to compile.
        k: The scale factor of the templates.
        observables: The observables to be included in the compiled circuit.
        custom_spec_rules: Custom specification rules for the cube specs.
        custom_substitute_rules: Custom substitution rules for the compiled blocks.

    Returns:
        The compiled stim circuit.
    """
    return _CompileHelper(
        block_graph, observables, custom_spec_rules, custom_substitute_rules
    ).compile_to_stim(k)


class _CompileHelper:
    """Helper class for compiling `BlockGraph` into `cirq.Circuit`."""

    def __init__(
        self,
        block_graph: BlockGraph,
        observables: list[AbstractObservable] | Literal["auto"] | None = "auto",
        custom_spec_rules: dict[CubeSpec, SpecRule] | None = None,
        custom_substitute_rules: dict[SubstitutionKey, SubstitutionRule] | None = None,
    ) -> None:
        if block_graph.num_open_ports != 0:
            raise TQECException(
                "Can not compile a block graph with open ports into circuits."
            )
        self.graph = block_graph
        self.abstract_observables = self.get_abstract_observables(observables)
        self.spec_rules = DEFAULT_SPEC_RULES | (custom_spec_rules or {})
        self.substitute_rules = DEFAULT_SUBSTITUTION_RULES | (
            custom_substitute_rules or {}
        )
        self.specs = self.get_cube_specs()

    def get_abstract_observables(
        self, observables: list[AbstractObservable] | Literal["auto"] | None
    ) -> list[AbstractObservable]:
        if observables is None:
            return []
        if observables == "auto":
            return self.graph.get_abstract_observables()
        return observables

    def compile_to_stim(self, k: int) -> stim.Circuit:
        cirq_circuit = self.compile_to_cirq(k)
        cirq_circuit = transform_to_stimcirq_compatible(cirq_circuit)
        return stimcirq.cirq_circuit_to_stim_circuit(cirq_circuit)

    def compile_to_cirq(self, k: int) -> cirq.Circuit:
        compiled_blocks = self.compile_blocks()
        block_size = self.inplace_scale_blocks_to(compiled_blocks, k)
        circuits = self.compile_cirq_circuits(compiled_blocks)
        self.inplace_add_observables(circuits, block_size)
        return self.assemble_circuits(circuits)

    def compile_blocks(self) -> dict[Position3D, CompiledBlock]:
        compiled_blocks = self.compile_base_blocks()
        self.inplace_apply_substitution_rules(compiled_blocks)
        return compiled_blocks

    def inplace_add_observables(
        self, assembled_circuits: dict[int, list[cirq.Circuit]], block_size: int
    ) -> None:
        """Inplace add the observable components to the circuits."""
        for i, observable in enumerate(self.abstract_observables):
            # Add the stabilizer region measurements to the end of the first layer of circuits at z.
            for pipe in observable.bottom_regions:
                z = pipe.u.position.z
                stabilizer_qubits = get_stabilizer_region_qubits_for_pipe(
                    pipe, block_size
                )
                observables = [
                    make_observable(
                        measurements=[Measurement(q, -1) for q in stabilizer_qubits],
                        observable_index=i,
                    )
                ]
                assembled_circuits[z][0].append(observables, cirq.InsertStrategy.INLINE)
            # Add the line measurements to the end of the last layer of circuits at z.
            for cube_or_pipe in observable.top_lines:
                if isinstance(cube_or_pipe, Cube):
                    qubits = get_midline_qubits_for_cube(cube_or_pipe, block_size)
                    z = cube_or_pipe.position.z
                else:
                    qubits = [
                        get_center_qubit_at_horizontal_pipe(cube_or_pipe, block_size)
                    ]
                    z = cube_or_pipe.u.position.z
                observables = [
                    make_observable(
                        measurements=[Measurement(q, -1) for q in qubits],
                        observable_index=i,
                    )
                ]
                assembled_circuits[z][-1].append(
                    observables, cirq.InsertStrategy.INLINE
                )

    @staticmethod
    def inplace_scale_blocks_to(blocks: dict[Position3D, CompiledBlock], k: int) -> int:
        """Scale the compiled blocks to the given scale `k` and return the
        scaled block size."""
        for block in blocks.values():
            block.scale_to(k)
        return _CompileHelper.get_uniform_block_size(blocks)

    @staticmethod
    def get_uniform_block_size(blocks: dict[Position3D, CompiledBlock]) -> int:
        """Get the uniform block size from the compiled blocks."""
        block_sizes = {block.size for block in blocks.values()}
        assert (
            len(block_sizes) == 1
        ), "All the blocks must have the same size after scaling."
        return block_sizes.pop()

    @staticmethod
    def compile_cirq_circuits(
        blocks: dict[Position3D, CompiledBlock],
    ) -> dict[int, list[cirq.Circuit]]:
        """Compile the blocks into `cirq.Circuit`s.

        Returns:
            A dictionary with the time position as the key and a list of `cirq.Circuit`s
            at that time position as the value. The circuits within the list correspond
            to different layers at the same time position.
        """
        block_size = _CompileHelper.get_uniform_block_size(blocks)
        min_z = min(pos.z for pos in blocks.keys())
        max_z = max(pos.z for pos in blocks.keys())
        circuits: dict[int, list[cirq.Circuit]] = {}
        for pos_z in range(min_z, max_z + 1):
            blocks_at_z = {pos: blocks[pos] for pos in blocks if pos.z == pos_z}
            num_layers = {block.num_layers for block in blocks_at_z.values()}
            if len(num_layers) != 1:
                raise TQECWarning(
                    "Not all the blocks on the same z-plane have the same number of layers."
                )
            circuits_at_z: list[cirq.Circuit] = []
            for i in range(max(num_layers)):
                circuits_at_layer: list[ScheduledCircuit] = []
                repetitions: set[int] = set()
                for pos, block in blocks_at_z.items():
                    if i >= block.num_layers:
                        continue
                    layer = block.layers[i]
                    if isinstance(layer, RepeatedPlaquettes):
                        repetitions.add(layer.num_rounds(block.template.k))
                    else:  # 0 represents no repetition structure
                        repetitions.add(0)
                    if len(repetitions) > 1:
                        raise TQECException(
                            "All the block layers on the same z-plane must have the same repeating structure, i.e.",
                            "either all the layers are repeated and repeat for the same number of rounds or none",
                            "of them are repeated.",
                        )

                    block_circuit_at_layer = block.instantiate_layer(i)
                    # Need to use `qubit_map` on `ScheduledCircuit` instead of
                    # `transform_qubits` on `cirq.Circuit` to map the MeasurementKey correctly.
                    c = ScheduledCircuit(block_circuit_at_layer)
                    qubit_map = {
                        q: map_qubit_at_block(q, pos, block_size) for q in c.qubits
                    }
                    circuits_at_layer.append(c.map_to_qubits(qubit_map, inplace=True))
                circuit_at_layer = merge_scheduled_circuits(circuits_at_layer)

                if 0 not in repetitions:
                    circuit_at_layer = cirq.Circuit(
                        cirq.CircuitOperation(
                            circuit_at_layer.freeze(), list(repetitions)[0]
                        )
                    )
                circuits_at_z.append(circuit_at_layer)
            circuits[pos_z] = circuits_at_z
        return circuits

    @staticmethod
    def assemble_circuits(circuits: dict[int, list[cirq.Circuit]]) -> cirq.Circuit:
        """Assemble the circuits at different time positions and different
        layers into a single circuit."""
        sorted_z = sorted(circuits.keys())
        circuits_at_zs = []
        for z in sorted_z:
            circuits_at_z = circuits[z]
            circuits_at_zs.append(sum(circuits_at_z, cirq.Circuit()))
        return sum(circuits_at_zs, cirq.Circuit())

    def get_cube_specs(self) -> dict[Position3D, CubeSpec]:
        """Get the specification of each cube in the block graph."""
        specs: dict[Position3D, CubeSpec] = {}
        for cube in self.graph.cubes:
            specs[cube.position] = CubeSpec.from_cube(cube, self.graph)
        return specs

    def compile_base_blocks(self) -> dict[Position3D, CompiledBlock]:
        """Get the base compiled blocks before applying the substitution
        rules."""
        compiled_blocks: dict[Position3D, CompiledBlock] = {}
        for cube in self.graph.cubes:
            spec = self.specs[cube.position]
            spec_rule = self.spec_rules[spec]
            compiled_blocks[cube.position] = spec_rule(spec)
        return compiled_blocks

    def inplace_apply_substitution_rules(
        self, blocks: dict[Position3D, CompiledBlock]
    ) -> None:
        """Apply the substitution rules to the compiled blocks inplace."""
        pipes = self.graph.pipes
        time_pipes = [
            pipe for pipe in pipes if pipe.pipe_type.direction == Direction3D.Z
        ]
        space_pipes = [
            pipe for pipe in pipes if pipe.pipe_type.direction != Direction3D.Z
        ]
        # Note that the order of the pipes to apply the substitution rules is important.
        # To keep the time-direction substitution rules from removing the extra resets
        # added by the space-direction substitution rules, we first apply the time-direction
        # substitution rules.
        for pipe in time_pipes + space_pipes:
            pos1, pos2 = pipe.u.position, pipe.v.position
            key = SubstitutionKey(self.specs[pos1], self.specs[pos2], pipe.pipe_type)
            rule = self.substitute_rules[key]
            blocks[pos1], blocks[pos2] = rule(key, blocks[pos1], blocks[pos2])
