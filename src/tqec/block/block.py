from __future__ import annotations

import typing as ty
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass

import cirq
import cirq.circuits
from typing_extensions import override

from tqec.block.enums import BlockDimension
from tqec.circuit.circuit import generate_circuit
from tqec.circuit.operations.measurement import Measurement, RepeatedMeasurement
from tqec.circuit.schedule import ScheduledCircuit, merge_scheduled_circuits
from tqec.exceptions import TQECException
from tqec.plaquette.library.empty import empty_square_plaquette
from tqec.plaquette.plaquette import Plaquette, Plaquettes
from tqec.position import Position3D
from tqec.templates import Template
from tqec.templates.interval import Interval
from tqec.templates.scale import LinearFunction, round_or_fail

_DEFAULT_BLOCK_REPETITIONS = LinearFunction(2, 1)


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
        pass

    @abstractmethod
    def instantiate(self) -> cirq.Circuit:
        """Return the full circuit representation of the computational
        block."""
        pass

    @abstractmethod
    def instantiate_without_boundary(self, boundary: BlockDimension) -> cirq.Circuit:
        """Return the circuit representation of the computational block without
        the specified boundary."""
        pass

    @abstractmethod
    def scale_to(self, k: int) -> None:
        """Scale the block to the provided scale factor."""
        pass


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
    return max(max(p.circuit.schedule, default=0) for p in plaquettes)


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
            self.plaquettes | plaquettes_to_update, self.repetitions
        )


@dataclass
class TemporalPlaquetteSequence:
    """Represent a temporal sequence of plaquettes with well defined boundaries
    in the time dimension."""

    initial_plaquettes: Plaquettes
    repeating_plaquettes: RepeatedPlaquettes | None
    final_plaquettes: Plaquettes

    def without_time_boundaries(self) -> TemporalPlaquetteSequence:
        return TemporalPlaquetteSequence(
            Plaquettes(defaultdict(empty_square_plaquette)),
            deepcopy(self.repeating_plaquettes),
            Plaquettes(defaultdict(empty_square_plaquette)),
        )

    def with_updated_plaquettes(
        self, plaquettes_to_update: dict[int, Plaquette]
    ) -> TemporalPlaquetteSequence:
        repeating_plaquettes = None
        if self.repeating_plaquettes is not None:
            repeating_plaquettes = self.repeating_plaquettes.with_updated_plaquettes(
                plaquettes_to_update
            )
        return TemporalPlaquetteSequence(
            self.initial_plaquettes | plaquettes_to_update,
            repeating_plaquettes,
            self.final_plaquettes | plaquettes_to_update,
        )


@dataclass
class StandardComputationBlock(ComputationBlock):
    """This class implements what we call the "standard" computational block.

    The standard computational block is composed of 3 distinct layers:

    1. an initialisation layer,
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

    template: Template
    plaquettes: TemporalPlaquetteSequence

    def __post_init__(self) -> None:
        expected_plaquette_number = self.template.expected_plaquettes_number
        if (
            not self.initial_plaquettes.has_default
            and len(self.initial_plaquettes) != expected_plaquette_number
        ):
            raise TQECException(
                f"Could not instantiate a ComputationBlock with {len(self.initial_plaquettes)} "
                f"initial plaquettes and a template that requires {expected_plaquette_number} "
                "plaquettes."
            )
        if (
            not self.final_plaquettes.has_default
            and len(self.final_plaquettes) != expected_plaquette_number
        ):
            raise TQECException(
                f"Could not instantiate a ComputationBlock with {len(self.final_plaquettes)} "
                f"final plaquettes and a template that requires {expected_plaquette_number} "
                "plaquettes."
            )
        if (
            self.repeating_plaquettes is not None
            and not self.repeating_plaquettes.plaquettes.has_default
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
        self, boundary: BlockDimension
    ) -> StandardComputationBlock:
        # Handle the time dimension as an edge case.
        if boundary == BlockDimension.Z:
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
    def instantiate_without_boundary(self, boundary: BlockDimension) -> cirq.Circuit:
        return self.replace_boundary_with_empty_plaquettes(boundary).instantiate()

    @override
    def scale_to(self, k: int) -> None:
        self.template.scale_to(k)

    @staticmethod
    def _get_measurements(
        template: Template, plaquettes: Plaquettes
    ) -> ty.Iterator[Measurement]:
        template_array = template.instantiate()
        default_increments = template.get_increments()

        for i, row in enumerate(template_array):
            for j, plaquette_index in enumerate(row):
                xoffset = j * default_increments.x
                yoffset = i * default_increments.y
                yield from (
                    m.offset_spatially_by(xoffset, yoffset)
                    for m in plaquettes[plaquette_index].measurements
                )

    @property
    def measurements(self) -> frozenset[Measurement | RepeatedMeasurement]:
        """Returns all the measurements in the block, relative to the end of
        the block."""
        measurement_number_by_qubits: dict[cirq.GridQubit, int] = {}
        all_measurements: list[Measurement | RepeatedMeasurement] = []
        # Start by the final measurements.
        for final_measurement in self._get_measurements(
            self.template, self.final_plaquettes
        ):
            all_measurements.append(final_measurement)
            measurement_number_by_qubits[final_measurement.qubit] = 1
        # Continue with the repeating measurements
        if self.repeating_plaquettes is not None:
            repetitions = self.repeating_plaquettes.number_of_rounds(self.template.k)
            for repeating_measurement in self._get_measurements(
                self.template, self.repeating_plaquettes.plaquettes
            ):
                qubit = repeating_measurement.qubit
                past_measurement_number = measurement_number_by_qubits.get(qubit, 0)
                all_measurements.append(
                    RepeatedMeasurement(
                        qubit,
                        Interval(
                            -past_measurement_number - repetitions,
                            -past_measurement_number,
                            start_excluded=False,
                            end_excluded=True,
                        ),
                    )
                )
                measurement_number_by_qubits[repeating_measurement.qubit] = (
                    past_measurement_number + repetitions
                )
        # Finish with the initial measurements
        for initial_measurement in self._get_measurements(
            self.template, self.initial_plaquettes
        ):
            qubit = repeating_measurement.qubit
            past_measurement_number = measurement_number_by_qubits.get(qubit, 0)
            all_measurements.append(
                initial_measurement.offset_temporally_by(-past_measurement_number)
            )

        return frozenset(all_measurements)

    @property
    def all_measurements(self) -> list[Measurement]:
        measurements: list[Measurement] = []
        for m in self.measurements:
            if isinstance(m, Measurement):
                measurements.append(m)
            else:  # isinstance(m, RepeatedMeasurement):
                measurements.extend(m.measurements())
        return measurements


@dataclass
class Computation:
    """Represents a topological quantum error corrected computation.

    The computation is represented by a mapping from a position to the
    computational block whose origin is located at that position.
    """

    blocks: dict[Position3D, ComputationBlock]

    def to_circuit(self) -> cirq.Circuit:
        """Build and return the quantum circuit representing the computation.

        Raises:
            TQECException: if any of the circuits obtained by instantiating the
                computational blocks is contains a qubit that is not a cirq.GridQubit.

        Returns:
            a cirq.Circuit instance representing the full computation.
        """
        instantiated_scheduled_blocks: list[ScheduledCircuit] = []
        for position, block in self.blocks.items():

            def shift_qubits(q: cirq.Qid) -> cirq.GridQubit:
                if not isinstance(q, cirq.GridQubit):
                    raise TQECException(
                        f"Found a circuit with {q} that is not a cirq.GridQubit instance."
                    )
                return q + (position.x, position.y)

            spatially_shifted_circuit = block.instantiate().transform_qubits(
                shift_qubits
            )
            instantiated_scheduled_blocks.append(
                ScheduledCircuit(spatially_shifted_circuit, position.z)
            )

        return merge_scheduled_circuits(instantiated_scheduled_blocks)
