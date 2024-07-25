from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass

import cirq
import cirq.circuits
from tqec.circuit.circuit import generate_circuit
from tqec.circuit.schedule import ScheduledCircuit, merge_scheduled_circuits
from tqec.exceptions import TQECException
from tqec.plaquette.plaquette import Plaquette
from tqec.templates.base import Template
from tqec.templates.scale import LinearFunction, round_or_fail
from typing_extensions import override


@dataclass
class Position3D:
    x: int
    y: int
    z: int


@dataclass
class ComputationBlock(ABC):
    """An abstract base class providing the necessary interface to implement a block.

    In theory, any block that might appear in a topological quantum error corrected
    computation should be representable by a structure that can implement the
    methods here.
    """

    @property
    @abstractmethod
    def needed_time(self) -> int:
        """Return the number of timesteps (`cirq.Moment`) needed by the block."""
        pass

    @abstractmethod
    def instantiate(self) -> cirq.Circuit:
        """Return the circuit representation of the computational block."""
        pass


def _number_of_moments_needed(plaquettes: list[Plaquette]) -> int:
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
    return max(max(p.circuit.schedule) for p in plaquettes)


@dataclass
class StandardComputationBlock(ComputationBlock):
    """This class implements what we call the "standard" computational block.

    The standard computational block is composed of 3 distinct layers:

    1. an initialisation layer,
    2. an (optional) repeated layer,
    3. a final layer.

    If the repeated layer is absent (i.e., it is `None`), then the block is a
    connector (the longer rectangular blocks in 3-dimensional SketchUp drawings).
    If the repeated layer is defined, then the block is "regular" (e.g., doing
    memory for n rounds).

    Raises:
        TQECException: if any of the provided plaquette lists do not contain
            exactly the right number of plaquettes, which is the expected number
            of plaquette of the provided template.
    """

    template: Template
    initial_plaquettes: list[Plaquette]
    final_plaquettes: list[Plaquette]
    repeating_plaquettes: tuple[list[Plaquette], LinearFunction] | None

    def __post_init__(self):
        expected_plaquette_number = self.template.expected_plaquettes_number
        if len(self.initial_plaquettes) != expected_plaquette_number:
            raise TQECException(
                f"Could not instantiate a ComputationBlock with {len(self.initial_plaquettes)} "
                f"initial plaquettes and a template that requires {expected_plaquette_number} "
                "plaquettes."
            )
        if len(self.final_plaquettes) != expected_plaquette_number:
            raise TQECException(
                f"Could not instantiate a ComputationBlock with {len(self.final_plaquettes)} "
                f"final plaquettes and a template that requires {expected_plaquette_number} "
                "plaquettes."
            )
        if (
            self.repeating_plaquettes is not None
            and len(self.repeating_plaquettes[0]) != expected_plaquette_number
        ):
            raise TQECException(
                f"Could not instantiate a ComputationBlock with {len(self.repeating_plaquettes)} "
                f"repeating plaquettes and a template that requires {expected_plaquette_number} "
                "plaquettes."
            )

    @property
    def is_connector(self) -> bool:
        """Check if the block is a connector or not."""
        return self.repeating_plaquettes is None

    @property
    @override
    def needed_time(self) -> int:
        time = _number_of_moments_needed(self.initial_plaquettes)
        if self.repeating_plaquettes is not None:
            plaquettes, f_repetitions = self.repeating_plaquettes
            repetitions = round_or_fail(f_repetitions(self.template.k))
            time += repetitions * _number_of_moments_needed(plaquettes)
        time += _number_of_moments_needed(self.final_plaquettes)
        return time

    @override
    def instantiate(self) -> cirq.Circuit:
        circuit = generate_circuit(self.template, self.initial_plaquettes)
        if self.repeating_plaquettes is not None:
            plaquettes, f_repetitions = self.repeating_plaquettes
            repetitions = round_or_fail(f_repetitions(self.template.k))
            inner_circuit = generate_circuit(self.template, plaquettes).freeze()
            circuit += cirq.CircuitOperation(inner_circuit, repetitions=repetitions)
        circuit += generate_circuit(self.template, self.final_plaquettes)
        return circuit


@dataclass
class Computation:
    """Represents a topological quantum error corrected computation.

    The computation is represented by a mapping from a position to the computational
    block whose origin is located at that position.
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
