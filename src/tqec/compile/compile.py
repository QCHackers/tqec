from dataclasses import dataclass
from typing import Literal
import cirq
import stim
import stimcirq

from tqec.circuit.operations.measurement import Measurement
from tqec.circuit.operations.operation import (
    Detector,
    make_observable,
    make_shift_coords,
)
from tqec.circuit.operations.transformer import transform_to_stimcirq_compatible
from tqec.circuit.schedule import ScheduledCircuit
from tqec.compile.detectors import compute_detectors_in_last_timestep
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
from tqec.exceptions import TQECException
from tqec.plaquette.plaquette import Plaquettes, RepeatedPlaquettes
from tqec.position import Direction3D, Position3D
from tqec.sketchup.block_graph import AbstractObservable, BlockGraph, Cube
from tqec.compile.block import CompiledBlock, TiledBlocks
from tqec.compile.specs import DEFAULT_SPEC_RULES, CubeSpec, SpecRule
from tqec.templates.scale import round_or_fail
from tqec.templates.tiled import TiledTemplate


@dataclass
class CompiledGraph:
    """Represents a compiled block graph.

    This class should be easy to scale and generate circuits directly.
    """

    block_graph: BlockGraph
    tiles_by_time: dict[int, TiledBlocks]

    def _check_equal_block_size(self) -> None:
        block_sizes = {tiles.block_size for tiles in self.tiles_by_time.values()}
        if len(block_sizes) != 1:
            raise TQECException("The block sizes of the compiled blocks are not equal.")

    def scale_to(self, k: int) -> None:
        """Scale the compiled graph to the given scale `k`."""
        for tiled_blocks in self.tiles_by_time.values():
            tiled_blocks.scale_to(k)
        self._check_equal_block_size()

    @property
    def block_size(self) -> int:
        self._check_equal_block_size()
        return next(iter(self.tiles_by_time.values())).block_size

    def generate_stim_circuit(
        self,
        k: int,
        observables: list[AbstractObservable] | Literal["auto"] | None = "auto",
        detection_radius: range | None = range(1, 2),
    ) -> stim.Circuit:
        """Generate the stim circuit from the compiled graph.

        Args:
            k: The scale factor of the templates.
            observables: The abstract observables to be included in the compiled circuit.
                If set to "auto", the observables will be automatically determined from the
                block graph. If a list of abstract observables is provided, only those
                observables will be included in the compiled circuit. If set to None, no
                observables will be included in the compiled circuit.
            detection_radius: The radius of the subtemplates to be used for the constructing
                detectors automatically.

        Returns:
            A compiled stim circuit.
        """
        cirq_circuit = self.generate_cirq_circuit(k, observables, detection_radius)
        cirq_circuit = transform_to_stimcirq_compatible(cirq_circuit)
        return stimcirq.cirq_circuit_to_stim_circuit(cirq_circuit)

    def generate_cirq_circuit(
        self,
        k: int,
        observables: list[AbstractObservable] | Literal["auto"] | None = "auto",
        detection_radius: range | None = range(1, 2),
    ) -> cirq.Circuit:
        """Generate the cirq circuit from the compiled graph.

        Args:
            k: The scale factor of the templates.
            observables: The abstract observables to be included in the compiled circuit.
                If set to "auto", the observables will be automatically determined from the
                block graph. If a list of abstract observables is provided, only those
                observables will be included in the compiled circuit. If set to None, no
                observables will be included in the compiled circuit.
            detection_radius: The radius of the subtemplates to be used for the constructing
                detectors automatically.

        Returns:
            A compiled cirq circuit.
        """
        self.scale_to(k)
        # assemble circuits time slice by time slice, layer by layer.
        circuits: dict[int, list[cirq.Circuit]] = {}
        for time, tiles in self.tiles_by_time.items():
            circuits[time] = [
                tiles.instantiate_layer(i) for i in range(tiles.num_layers)
            ]
            # construct detectors
            if detection_radius is None:
                continue
            detectors = _construct_detectors_by_layer(
                tiles.tiled_template, tiles.tiled_layers, detection_radius
            )
            for i, layer_detectors in enumerate(detectors):
                circuits[time][i].append(layer_detectors, cirq.InsertStrategy.INLINE)
                circuits[time][i].append(
                    make_shift_coords(0, 0, 1), cirq.InsertStrategy.INLINE
                )
        # construct observables
        _inplace_add_observables(
            circuits, self.get_abstract_observables(observables), self.block_size
        )
        # shift and merge circuits
        return self.shift_and_merge_circuits(circuits)

    def get_abstract_observables(
        self,
        observables: list[AbstractObservable] | Literal["auto"] | None = "auto",
    ) -> list[AbstractObservable]:
        """Get the abstract observables to be included in the compiled
        circuit."""
        if observables is None:
            return []
        if observables == "auto":
            return self.block_graph.get_abstract_observables()
        return observables

    def shift_and_merge_circuits(
        self, circuits: dict[int, list[cirq.Circuit]]
    ) -> cirq.Circuit:
        circuits_by_time = []
        ordered_times = sorted(circuits.keys())
        for t in ordered_times:
            circuits_at_t = []
            tiles = self.tiles_by_time[t]
            # We need to shift the circuit based on the shift of the tiled template.
            origin_shift = tiles.tiled_template.origin_shift
            for i in range(tiles.num_layers):
                circuit_before_shift = circuits[t][i]
                # Need to use `qubit_map` on `ScheduledCircuit` instead of
                # `transform_qubits` on `cirq.Circuit` to map the MeasurementKey correctly.
                scheduled = ScheduledCircuit(circuit_before_shift)
                qubit_map = {
                    q: q
                    + (
                        origin_shift.y * self.block_size * 2,
                        origin_shift.x * self.block_size * 2,
                    )
                    for q in scheduled.qubits
                }
                shifted_circuit = scheduled.map_to_qubits(
                    qubit_map, inplace=True
                ).raw_circuit
                layer = tiles.tiled_layers[i]
                if isinstance(layer, RepeatedPlaquettes):
                    shifted_circuit = cirq.Circuit(
                        cirq.CircuitOperation(
                            shifted_circuit.freeze(),
                            repetitions=round_or_fail(
                                layer.repetitions(tiles.tiled_template.k)
                            ),
                        )
                    )
                circuits_at_t.append(shifted_circuit)
            circuits_by_time.append(sum(circuits_at_t, cirq.Circuit()))
        return sum(circuits_by_time, cirq.Circuit())


def _construct_detectors_by_layer(
    template: TiledTemplate,
    layers: list[Plaquettes],
    subtemplate_radius_trial_range: range = range(1, 2),
) -> list[list[cirq.Operation]]:
    detectors_by_layer = []
    subsequent_layers: tuple[Plaquettes, Plaquettes] | tuple[Plaquettes]
    for i in range(len(layers)):
        if i == 0:
            subsequent_layers = (layers[0],)
        else:
            subsequent_layers = (layers[i - 1], layers[i])
        detectors = compute_detectors_in_last_timestep(
            template, subsequent_layers, subtemplate_radius_trial_range
        )
        detectors_by_layer.append(detectors)
    return detectors_by_layer


def _inplace_add_observables(
    circuits: dict[int, list[cirq.Circuit]],
    abstract_observables: list[AbstractObservable],
    block_size: int,
) -> None:
    """Inplace add the observable components to the circuits.

    The circuits are grouped by time slices and layers. The key of the
    circuits is the time coordinate and the value is a list of circuits
    at that time slice ordered by layers.
    """
    for i, observable in enumerate(abstract_observables):
        # Add the stabilizer region measurements to the end of the first layer of circuits at z.
        for pipe in observable.bottom_regions:
            z = pipe.u.position.z
            stabilizer_qubits = get_stabilizer_region_qubits_for_pipe(pipe, block_size)
            observables = [
                make_observable(
                    measurements=[Measurement(q, -1) for q in stabilizer_qubits],
                    observable_index=i,
                )
            ]
            circuits[z][0].append(observables, cirq.InsertStrategy.INLINE)
        # Add the line measurements to the end of the last layer of circuits at z.
        for cube_or_pipe in observable.top_lines:
            if isinstance(cube_or_pipe, Cube):
                qubits = get_midline_qubits_for_cube(cube_or_pipe, block_size)
                z = cube_or_pipe.position.z
            else:
                qubits = [get_center_qubit_at_horizontal_pipe(cube_or_pipe, block_size)]
                z = cube_or_pipe.u.position.z
            observables = [
                make_observable(
                    measurements=[Measurement(q, -1) for q in qubits],
                    observable_index=i,
                )
            ]
            circuits[z][-1].append(observables, cirq.InsertStrategy.INLINE)


def compile_block_graph(
    block_graph: BlockGraph,
    custom_spec_rules: dict[CubeSpec, SpecRule] | None = None,
    custom_substitute_rules: dict[SubstitutionKey, SubstitutionRule] | None = None,
) -> CompiledGraph:
    """Compile a block graph.

    Args:
        block_graph: The block graph to compile.
        custom_spec_rules: Custom specification rules for the cube specs. This is a dict
            mapping the cube specs to the corresponding spec rules. If not provided, the
            default spec rules will be used. Spec rules determine how to compile a cube
            spec into a compiled block, i.e which template to use and the specific plaquettes
            to use in the template.
        custom_substitute_rules: Custom substitution rules for the compiled blocks. This is
            a dict mapping the substitution keys to the corresponding substitution rules. If
            not provided, the default substitution rules will be used. Substitution rules
            determine how to substitute plaquettes in the two compiled blocks connected by a pipe.

    Returns:
        A `CompiledGraph` object that can be used to generate a cirq/stim circuit and scale easily.
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

    # 3. Collect by time and tile the blocks.
    min_z = min(pos.z for pos in blocks.keys())
    max_z = max(pos.z for pos in blocks.keys())
    tiles_in_time: dict[int, TiledBlocks] = {
        z: TiledBlocks(
            {pos.as_2d(): block for pos, block in blocks.items() if pos.z == z}
        )
        for z in range(min_z, max_z + 1)
    }
    return CompiledGraph(block_graph, tiles_in_time)
