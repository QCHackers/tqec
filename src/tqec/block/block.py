from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from functools import partial
from typing_extensions import override

import cirq
import cirq.circuits
import networkx as nx
from tqec.direction import Direction3D
from tqec.circuit.circuit import generate_circuit
from tqec.circuit.schedule import ScheduledCircuit, merge_scheduled_circuits
from tqec.exceptions import TQECException
from tqec.plaquette.library.empty import empty_square_plaquette
from tqec.plaquette.plaquette import Plaquette, Plaquettes
from tqec.position import Position3D
from tqec.templates.constructions.qubit import ComposedTemplateWithSides
from tqec.templates.scale import LinearFunction, round_or_fail


@dataclass
class ComputationBlock(ABC):
    """An abstract base class providing the necessary interface to implement a
    block.

    In theory, any block that might appear in a topological quantum
    error corrected computation should be representable by a structure
    that can implement the methods here.
    """

    @property
    @abstractmethod
    def depth(self) -> int:
        """Return the number of timesteps (`cirq.Moment`) needed by the
        block."""

    @abstractmethod
    def instantiate(self) -> cirq.Circuit:
        """Return the full circuit representation of the computational
        block."""

    @abstractmethod
    def instantiate_without_boundary(self, boundary: Direction3D) -> cirq.Circuit:
        """Return the circuit representation of the computational block without
        the specified boundary."""

    @abstractmethod
    def scale_to(self, k: int) -> None:
        """Scale the block to the provided scale factor."""


def _number_of_moments_needed(plaquettes: Plaquettes) -> int:
    """Return the number of `cirq.Moment` needed to execute all the provided
    plaquettes in parallel.

    This function returns the maximum scheduled time over all the provided
    plaquettes.

    Args:
        plaquettes: a list of plaquettes that should be executed in parallel.

    Returns:
        the number of `cirq.Moment` needed to execute the provided plaquettes
        in parallel.
    """
    all_plaquettes: typing.Iterable[Plaquette]
    if isinstance(plaquettes, list):
        all_plaquettes = plaquettes
    elif isinstance(plaquettes, typing.Mapping):
        all_plaquettes = plaquettes.values()
        if (
            isinstance(plaquettes, defaultdict)
            and plaquettes.default_factory is not None
        ):
            all_plaquettes = list(all_plaquettes) + [plaquettes.default_factory()]
    return max(max(p.circuit.schedule, default=0) for p in all_plaquettes)


def _plaquette_dict(
    plaquettes: Plaquettes,
) -> dict[int, Plaquette] | defaultdict[int, Plaquette]:
    if isinstance(plaquettes, (dict, defaultdict)):
        return plaquettes
    return dict(enumerate(plaquettes))


@dataclass
class RepeatedPlaquettes:
    """Represent plaquettes that should be repeated for several rounds."""

    plaquettes: Plaquettes
    repetitions: LinearFunction

    def __len__(self) -> int:
        return len(self.plaquettes)

    def number_of_rounds(self, k: int) -> int:
        return round_or_fail(self.repetitions(k))

    def with_updated_plaquettes(
        self, plaquettes_to_update: dict[int, Plaquette]
    ) -> RepeatedPlaquettes:
        return RepeatedPlaquettes(
            _plaquette_dict(self.plaquettes) | plaquettes_to_update, self.repetitions
        )


@dataclass
class TemporalPlaquetteSequence:
    """Represent a temporal sequence of plaquettes with well defined boundaries
    in the time dimension."""

    initial_plaquettes: Plaquettes
    repeating_plaquettes: RepeatedPlaquettes | None
    final_plaquettes: Plaquettes

    def without_time_boundaries(self) -> TemporalPlaquetteSequence:
        """Generate a new `TemporalPlaquetteSequence` without the time boundaries.

        Replaces the initial and final plaquettes with empty plaquettes.

        Returns:
            TemporalPlaquetteSequence: The new sequence.
        """
        return TemporalPlaquetteSequence(
            defaultdict(empty_square_plaquette),
            deepcopy(self.repeating_plaquettes),
            defaultdict(empty_square_plaquette),
        )

    def with_updated_plaquettes(
        self, plaquettes_to_update: dict[int, Plaquette]
    ) -> TemporalPlaquetteSequence:
        """Replaces the plaquettes in the sequence with the provided ones.

        If the current se
        Args:
            plaquettes_to_update (dict[int, Plaquette]): _description_

        Returns:
            TemporalPlaquetteSequence: _description_
        """
        repeating_plaquettes = None
        if self.repeating_plaquettes is not None:
            repeating_plaquettes = self.repeating_plaquettes.with_updated_plaquettes(
                plaquettes_to_update
            )
        return TemporalPlaquetteSequence(
            _plaquette_dict(self.initial_plaquettes) | plaquettes_to_update,
            repeating_plaquettes,
            _plaquette_dict(self.final_plaquettes) | plaquettes_to_update,
        )


@dataclass
class StandardComputationBlock(ComputationBlock):
    """This class implements what we call the "standard" computational block.

    The standard computational block is composed of 3 distinct layers:

    1. an initialization layer,
    2. an (optional) repeated layer,
    3. a final layer.

    If the repeated layer is absent (i.e., it is `None`), then the block is a
    connector (a `Pipe`).
    If the repeated layer is defined, then the block is a `Cube` (e.g., doing
    memory for n rounds).

    Raises:
        TQECException: if any of the provided plaquette lists do not contain
            exactly the right number of plaquettes, which is the expected number
            of plaquette of the provided template.
    """

    template: ComposedTemplateWithSides
    plaquettes: TemporalPlaquetteSequence

    def __post_init__(self) -> None:
        expected_plaquette_number = self.template.expected_plaquettes_number
        if (
            not isinstance(self.initial_plaquettes, defaultdict)
            and len(self.initial_plaquettes) != expected_plaquette_number
        ):
            raise TQECException(
                f"Could not instantiate a ComputationBlock with {len(self.initial_plaquettes)} "
                f"initial plaquettes and a template that requires {expected_plaquette_number} "
                "plaquettes."
            )
        if (
            not isinstance(self.final_plaquettes, defaultdict)
            and len(self.final_plaquettes) != expected_plaquette_number
        ):
            raise TQECException(
                f"Could not instantiate a ComputationBlock with {len(self.final_plaquettes)} "
                f"final plaquettes and a template that requires {expected_plaquette_number} "
                "plaquettes."
            )
        if (
            self.repeating_plaquettes is not None
            and not isinstance(self.repeating_plaquettes.plaquettes, defaultdict)
            and len(self.repeating_plaquettes.plaquettes) != expected_plaquette_number
        ):
            raise TQECException(
                f"Could not instantiate a ComputationBlock with {len(self.repeating_plaquettes)} "
                f"repeating plaquettes and a template that requires {expected_plaquette_number} "
                "plaquettes."
            )

    @property
    def initial_plaquettes(self) -> Plaquettes:
        return self.plaquettes.initial_plaquettes

    @property
    def repeating_plaquettes(self) -> RepeatedPlaquettes | None:
        return self.plaquettes.repeating_plaquettes

    @repeating_plaquettes.setter
    def repeating_plaquettes(self, value: RepeatedPlaquettes | None) -> None:
        self.plaquettes.repeating_plaquettes = value

    @property
    def final_plaquettes(self) -> Plaquettes:
        return self.plaquettes.final_plaquettes

    @property
    def is_connector(self) -> bool:
        """Check if the block is a connector or not."""
        return self.repeating_plaquettes is None

    @property
    @override
    def depth(self) -> int:
        time = _number_of_moments_needed(self.initial_plaquettes)
        if self.repeating_plaquettes is not None:
            repetitions = self.repeating_plaquettes.number_of_rounds(self.template.k)
            time += repetitions * _number_of_moments_needed(
                self.repeating_plaquettes.plaquettes
            )
        time += _number_of_moments_needed(self.final_plaquettes)
        return time

    def replace_boundary_with_empty_plaquettes(
        self, boundary: Direction3D
    ) -> StandardComputationBlock:
        # Handle the time dimension as an edge case.
        if boundary == Direction3D.Z:
            return StandardComputationBlock(
                self.template, self.plaquettes.without_time_boundaries()
            )

        # For the spatial dimensions, get the indices of the plaquettes that should be
        # replaced by an empty plaquette.
        sides_to_replace = boundary.to_template_sides()
        plaquette_indices_to_replace = self.template.get_plaquette_indices_on_sides(
            sides_to_replace
        )
        plaquettes_to_replace = {
            i: empty_square_plaquette() for i in plaquette_indices_to_replace
        }
        # Return the resulting block.
        return StandardComputationBlock(
            self.template,
            self.plaquettes.with_updated_plaquettes(plaquettes_to_replace),
        )

    @override
    def instantiate(self) -> cirq.Circuit:
        circuit = generate_circuit(self.template, self.initial_plaquettes)
        if self.repeating_plaquettes is not None:
            repetitions = self.repeating_plaquettes.number_of_rounds(self.template.k)
            plaquettes = self.repeating_plaquettes.plaquettes
            inner_circuit = generate_circuit(self.template, plaquettes).freeze()
            circuit += cirq.CircuitOperation(inner_circuit, repetitions=repetitions)
        circuit += generate_circuit(self.template, self.final_plaquettes)
        return circuit

    @override
    def instantiate_without_boundary(self, boundary: Direction3D) -> cirq.Circuit:
        return self.replace_boundary_with_empty_plaquettes(boundary).instantiate()

    @override
    def scale_to(self, k: int) -> None:
        self.template.scale_to(k)


_COMPUTATION_DATA_KEY = "tqec_computation_block"


# @dataclass
class Computation:
    """Represents a topological quantum error corrected computation.

    The computation is represented by a mapping from a position to the
    computational block whose origin is located at that position.
    """

    def __init__(self, blocks: dict[Position3D, ComputationBlock]) -> None:
        self.blocks = blocks
        self._graph = nx.Graph()
        for position, block in blocks.items():
            self._graph.add_node(position, **{_COMPUTATION_DATA_KEY: block})

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


def _shift_qubits(position: Position3D, q: cirq.Qid) -> cirq.GridQubit:
    if not isinstance(q, cirq.GridQubit):
        raise TQECException(
            f"Found a circuit with {q} that is not a cirq.GridQubit instance."
        )
    return q + (position.x, position.y)
