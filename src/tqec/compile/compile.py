import itertools
from dataclasses import dataclass
from time import perf_counter
from typing import Literal, Mapping, Sequence

import stim

from tqec.circuit.measurement_map import MeasurementRecordsMap
from tqec.circuit.qubit_map import QubitMap
from tqec.circuit.schedule import ScheduledCircuit
from tqec.compile.block import BlockLayout, CompiledBlock
from tqec.compile.detectors.compute import compute_detectors_for_fixed_radius
from tqec.compile.detectors.database import DetectorDatabase
from tqec.compile.observables import inplace_add_observables
from tqec.compile.specs import CubeSpec, SpecRule
from tqec.compile.specs.library.css import CSS_SPEC_RULES
from tqec.compile.substitute import (
    DEFAULT_SUBSTITUTION_RULES,
    SubstitutionKey,
    SubstitutionRule,
)
from tqec.computation.block_graph import AbstractObservable, BlockGraph
from tqec.exceptions import TQECException
from tqec.noise_models import NoiseModel
from tqec.plaquette.plaquette import Plaquettes, RepeatedPlaquettes
from tqec.position import Direction3D, Displacement, Position3D
from tqec.scale import round_or_fail
from tqec.templates.base import Template
from tqec.templates.layout import LayoutTemplate


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
            raise TQECException("The compiled graph includes no observable.")

    def generate_stim_circuit(
        self, k: int, noise_model: NoiseModel | None = None, manhattan_radius: int = 2
    ) -> stim.Circuit:
        """Generate the stim circuit from the compiled graph.

        Args:
            k: The scale factor of the templates.
            noise_models: The noise models to be applied to the circuit.

        Returns:
            A compiled stim circuit.
        """
        # Generate the quantum circuits, time slice by time slice, layer by layer.
        # Note that the circuits have to be shifted to their correct position.
        circuits: list[list[ScheduledCircuit]] = []
        for layout in self.layout_slices:
            circuits.append(layout.get_shifted_circuits(k))
        # The generated circuits cannot, for the moment, be merged together because
        # the qubit indices used are likely inconsistent between circuits (a given
        # index `i` might be used for different qubits in different circuits).
        # Fix that now so that we do not have to think about it later.
        global_qubit_map = self._relabel_circuits_qubit_indices_inplace(circuits)

        # Construct the observables and add them in-place to the built circuits.
        inplace_add_observables(
            circuits,
            [layout.template for layout in self.layout_slices],
            self.observables,
            k,
        )

        # Compute the detectors and add them in-place in circuits
        flattened_circuits: list[ScheduledCircuit] = sum(circuits, start=[])
        flattened_templates: list[LayoutTemplate] = sum(
            (
                [layout.template for _ in range(layout.num_layers)]
                for layout in self.layout_slices
            ),
            start=[],
        )
        flattened_plaquettes: list[Plaquettes] = sum(
            (layout.layers for layout in self.layout_slices), start=[]
        )
        self._inplace_add_detectors_to_circuits(
            flattened_circuits,
            flattened_templates,
            flattened_plaquettes,
            k,
            manhattan_radius,
        )
        # Assemble the circuits.
        circuit = global_qubit_map.to_circuit()
        for circ, plaq in zip(flattened_circuits[:-1], flattened_plaquettes[:-1]):
            if isinstance(plaq, RepeatedPlaquettes):
                circuit += circ.get_repeated_circuit(
                    round_or_fail(plaq.repetitions(k)), include_qubit_coords=False
                )
            else:
                circuit += circ.get_circuit(include_qubit_coords=False)
            circuit.append("TICK", [], [])
        circuit += flattened_circuits[-1].get_circuit(include_qubit_coords=False)

        # If provided, apply the noise model.
        if noise_model is not None:
            circuit = noise_model.noisy_circuit(circuit)
        return circuit

    @staticmethod
    def _relabel_circuits_qubit_indices_inplace(
        circuits: Sequence[Sequence[ScheduledCircuit]],
    ) -> QubitMap:
        used_qubits = frozenset(
            # Using itertools to avoid the edge case where there is no circuit
            itertools.chain.from_iterable(
                [c.qubits for clayer in circuits for c in clayer]
            )
        )
        global_qubit_map = QubitMap.from_qubits(sorted(used_qubits))
        global_q2i = global_qubit_map.q2i
        for circuit in itertools.chain.from_iterable(circuits):
            local_indices_to_global_indices = {
                local_index: global_q2i[q]
                for local_index, q in circuit.qubit_map.items()
            }
            circuit.map_qubit_indices(local_indices_to_global_indices, inplace=True)
        return global_qubit_map

    @staticmethod
    def _inplace_add_detectors_to_circuits(
        circuits: Sequence[ScheduledCircuit],
        templates: Sequence[Template],
        plaquettes: Sequence[Plaquettes],
        k: int,
        manhattan_radius: int = 2,
    ) -> None:
        # Start with the first circuit, as this is a special case.
        first_template = templates[0]
        first_plaquettes = plaquettes[0]
        first_slice_detectors = compute_detectors_for_fixed_radius(
            (first_template,), k, (first_plaquettes,), manhattan_radius
        )
        # Initialise the measurement records map with the first circuit.
        mrecords_map = MeasurementRecordsMap.from_scheduled_circuit(circuits[0])
        # Add the detectors to the first circuit
        for d in first_slice_detectors:
            circuits[0].append_annotation(d.to_instruction(mrecords_map))

        # Now, iterate over all the pairs of circuits.
        for i in range(1, len(circuits)):
            current_circuit = circuits[i]
            start = perf_counter()
            slice_detectors = compute_detectors_for_fixed_radius(
                (templates[i - 1], templates[i]),
                k,
                (plaquettes[i - 1], plaquettes[i]),
                manhattan_radius,
            )
            end = perf_counter()
            print(
                f"Found {len(slice_detectors)} detectors in {end-start:.2f} "
                f"seconds for slice {i}."
            )
            mrecords_map = mrecords_map.with_added_measurements(
                MeasurementRecordsMap.from_scheduled_circuit(current_circuit)
            )
            for d in slice_detectors:
                current_circuit.append_annotation(d.to_instruction(mrecords_map))
        # We are now over, all the detectors should be added inplace to the end
        # of the last circuit containing a measurement involved in the detector.


def compile_block_graph(
    block_graph: BlockGraph,
    spec_rules: Mapping[CubeSpec, SpecRule] = CSS_SPEC_RULES,
    substitute_rules: Mapping[
        SubstitutionKey, SubstitutionRule
    ] = DEFAULT_SUBSTITUTION_RULES,
    observables: list[AbstractObservable] | Literal["auto"] | None = "auto",
) -> CompiledGraph:
    """Compile a block graph.

    Args:
        block_graph: The block graph to compile.
        spec_rules: Custom specification rules for the cube specs. This is a dict
            mapping the cube specs to the corresponding spec rules. Spec rules
            determine how to compile a cube spec into a compiled block, i.e
            which template to use and the specific plaquettes to use in the
            template. The default spec rules are the CSS surface code spec rules.
        substitute_rules: Custom substitution rules for the compiled blocks. This
            is a dict mapping the substitution keys to the corresponding substitution
            rules. Substitution rules determine how to substitute plaquettes in
            the two compiled blocks connected by a pipe.
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
