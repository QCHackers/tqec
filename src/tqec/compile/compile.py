from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal
import cirq
import stim
import stimcirq

from tqec.circuit.operations.transformer import transform_to_stimcirq_compatible
from tqec.circuit.schedule import ScheduledCircuit
from tqec.compile.substitute import (
    SubstitutionKey,
    SubstitutionRule,
    DEFAULT_SUBSTITUTION_RULES,
)
from tqec.exceptions import TQECException, TQECWarning
from tqec.noise_models.base import BaseNoiseModel
from tqec.plaquette.plaquette import RepeatedPlaquettes
from tqec.position import Direction3D, Position3D
from tqec.sketchup.block_graph import AbstractObservable, BlockGraph
from tqec.compile.block import CompiledBlock, BlockLayout
from tqec.compile.specs import DEFAULT_SPEC_RULES, CubeSpec, SpecRule
from tqec.compile.observables import inplace_add_observables
from tqec.templates.scale import round_or_fail


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
        if len(self.observables) == 0:
            raise TQECWarning("The compiled graph includes no observable.")

    def scale_to(self, k: int) -> None:
        """Scale the compiled graph to the given scale `k`."""
        for layout in self.layout_slices:
            layout.scale_to(k)

    def generate_stim_circuit(
        self,
        k: int,
        noise_models: Iterable[BaseNoiseModel] = (),
    ) -> stim.Circuit:
        """Generate the stim circuit from the compiled graph.

        Args:
            k: The scale factor of the templates.
            noise_models: The noise models to be applied to the circuit.

            A compiled stim circuit.
        """
        cirq_circuit = self.generate_cirq_circuit(k, noise_models)
        cirq_circuit = transform_to_stimcirq_compatible(cirq_circuit)
        return stimcirq.cirq_circuit_to_stim_circuit(cirq_circuit)

    def generate_cirq_circuit(
        self,
        k: int,
        noise_models: Iterable[BaseNoiseModel] = (),
    ) -> cirq.Circuit:
        """Generate the cirq circuit from the compiled graph.

        Args:
            k: The scale factor of the templates.
            noise_models: The noise models to be applied to the circuit.

        Returns:
            A compiled cirq circuit.
        """
        self.scale_to(k)
        # assemble circuits time slice by time slice, layer by layer.
        circuits: list[list[cirq.Circuit]] = []
        for layout in self.layout_slices:
            circuits.append(
                [layout.instantiate_layer(i) for i in range(layout.num_layers)]
            )
        # construct observables
        inplace_add_observables(
            circuits,
            [layout.template for layout in self.layout_slices],
            self.observables,
        )
        # shift and merge circuits
        circuit = self._shift_and_merge_circuits(circuits)
        # apply noise models
        for noise_model in noise_models:
            circuit = circuit.with_noise(noise_model)
        return circuit

    def _shift_and_merge_circuits(
        self, circuits: list[list[cirq.Circuit]]
    ) -> cirq.Circuit:
        circuits_by_time = []
        for t, layout in enumerate(self.layout_slices):
            circuits_at_t = []
            # We need to shift the circuit based on the shift of the layout template.
            origin_shift = layout.template.origin_shift
            element_shape = layout.template.element_shape
            increment = layout.template.get_increments()
            for i in range(layout.num_layers):
                circuit_before_shift = circuits[t][i]
                # Need to use `qubit_map` on `ScheduledCircuit` instead of
                # `transform_qubits` on `cirq.Circuit` to map the MeasurementKey correctly.
                scheduled = ScheduledCircuit(circuit_before_shift)
                qubit_map = {
                    q: q
                    + (
                        origin_shift.y * element_shape.y * increment.y,
                        origin_shift.x * element_shape.x * increment.x,
                    )
                    for q in scheduled.qubits
                }
                shifted_circuit = scheduled.map_to_qubits(
                    qubit_map, inplace=True
                ).raw_circuit
                layer = layout.layers[i]
                if isinstance(layer, RepeatedPlaquettes):
                    shifted_circuit = cirq.Circuit(
                        cirq.CircuitOperation(
                            shifted_circuit.freeze(),
                            repetitions=round_or_fail(
                                layer.repetitions(layout.template.k)
                            ),
                        )
                    )
                circuits_at_t.append(shifted_circuit)
            circuits_by_time.append(sum(circuits_at_t, cirq.Circuit()))
        return sum(circuits_by_time, cirq.Circuit())


def compile_block_graph(
    block_graph: BlockGraph,
    observables: list[AbstractObservable] | Literal["auto"] | None = "auto",
    custom_spec_rules: dict[CubeSpec, SpecRule] | None = None,
    custom_substitute_rules: dict[SubstitutionKey, SubstitutionRule] | None = None,
) -> CompiledGraph:
    """Compile a block graph.

    Args:
        block_graph: The block graph to compile.
        observables: The abstract observables to be included in the compiled
            circuit.
            If set to "auto", the observables will be automatically determined from
            the block graph. If a list of abstract observables is provided, only
            those observables will be included in the compiled circuit. If set to
            None, no observables will be included in the compiled circuit.
        custom_spec_rules: Custom specification rules for the cube specs. This is a dict
            mapping the cube specs to the corresponding spec rules. If not provided, the
            default spec rules will be used. Spec rules determine how to compile a cube
            spec into a compiled block, i.e which template to use and the specific
            plaquettes to use in the template.
        custom_substitute_rules: Custom substitution rules for the compiled blocks. This
            is a dict mapping the substitution keys to the corresponding substitution
            rules. If not provided, the default substitution rules will be used.
            Substitution rules determine how to substitute plaquettes in the two
            compiled blocks connected by a pipe.

    Returns:
        A `CompiledGraph` object that can be used to generate a cirq/stim circuit and
        scale easily.
    """
    if block_graph.num_open_ports != 0:
        raise TQECException(
            "Can not compile a block graph with open ports into circuits."
        )
    spec_rules = DEFAULT_SPEC_RULES | (custom_spec_rules or {})
    substitute_rules = DEFAULT_SUBSTITUTION_RULES | (custom_substitute_rules or {})
    cube_specs = {
        cube: CubeSpec.from_cube(cube, block_graph) for cube in block_graph.cubes
    }

    # 0. Set the minimum z of block graph to 0.(time starts from zero)
    block_graph = block_graph.with_zero_min_z()

    # 1. Get the base compiled blocks before applying the substitution rules.
    blocks: dict[Position3D, CompiledBlock] = {}
    for cube in block_graph.cubes:
        spec = cube_specs[cube]
        spec_rule = spec_rules[spec]
        blocks[cube.position] = spec_rule(spec)

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
        key = SubstitutionKey(cube_specs[pipe.u], cube_specs[pipe.v], pipe.pipe_type)
        rule = substitute_rules[key]
        blocks[pos1], blocks[pos2] = rule(key, blocks[pos1], blocks[pos2])

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
        obs_included = block_graph.get_abstract_observables()
    else:
        obs_included = observables

    return CompiledGraph(layout_slices, obs_included)
