from __future__ import annotations

import typing as ty
from collections import defaultdict
from copy import deepcopy

import cirq
import cirq.circuits
import numpy
import numpy.typing as npt

from tqec.circuit.schedule import ScheduledCircuit, merge_scheduled_circuits
from tqec.exceptions import TQECException
from tqec.plaquette.plaquette import Plaquette
from tqec.position import Displacement
from tqec.templates.base import Template


def generate_circuit(
    template: Template,
    plaquettes: list[Plaquette] | dict[int, Plaquette] | defaultdict[int, Plaquette],
) -> cirq.Circuit:
    """Generate a quantum circuit from a template and its plaquettes.

    This is one of the core methods of the `tqec` package. It generates a quantum circuit
    from the description of the template that should be implemented as well as the plaquettes
    that should be used to instantiate the provided template.

    This function requires that a few pre-conditions on the inputs are met:
    1. the number of plaquettes provided should match the number of plaquettes required by
    the provided template.
    2. all the provided plaquettes should be implemented on cirq.GridQubit instances **only**.

    If any of the above pre-conditions is not met, the inputs are considered invalid, in which
    case this function **might** raise an error.

    Args:
        template: spatial description of the quantum error correction experiment
            we want to implement.
        plaquettes: description of the computation that should happen at
            different time-slices of the quantum error correction experiment (or
            at least part of it). If provided as a dictionary, plaquettes should be
            1-indexed (i.e., ``0 not in plaquettes`` should be ``True``).

    Returns:
        a cirq.Circuit instance implementing the (part of) quantum error
        correction experiment represented by the provided inputs.

    Raises:
        TQECException: if ``len(plaquettes) != template.expected_plaquettes_number`` or
            if plaquettes is provided as a dictionary and ``0 in plaquettes``.
    """
    # Check that the user gave enough plaquettes.
    if (
        not isinstance(plaquettes, defaultdict)
        and len(plaquettes) != template.expected_plaquettes_number
    ):
        raise TQECException(
            f"{len(plaquettes)} plaquettes have been provided, but "
            f"{template.expected_plaquettes_number} were expected."
        )
    if isinstance(plaquettes, ty.Mapping) and 0 in plaquettes:
        raise TQECException(
            "If using a dictionary, the input plaquettes parameter should not "
            f"contain the entry 0. Found a value ({plaquettes[0]}) at entry 0."
        )

    # instantiate the template with the appropriate plaquette indices.
    # Index 0 is "no plaquette" by convention and should not be included here.
    _indices = list(range(1, template.expected_plaquettes_number + 1))
    template_plaquettes = template.instantiate(_indices)
    increments = template.get_increments()

    return generate_circuit_from_instantiation(
        template_plaquettes, plaquettes, increments
    )


def generate_circuit_from_instantiation(
    plaquette_array: npt.NDArray[numpy.int_],
    plaquettes: Plaquettes,
    increments: Displacement,
) -> cirq.Circuit:
    """Generate a quantum circuit from an array of plaquette indices and the
    associated plaquettes.

    This is one of the core methods of the `tqec` package. It generates a quantum circuit
    from a spatial description of where the plaquettes should be located as well as the
    actual plaquettes used.

    This function requires that a few pre-conditions on the inputs are met:
    1. the number of plaquettes provided should match the number of plaquettes required by
    the provided template.
    2. all the provided plaquettes should be implemented on cirq.GridQubit instances **only**.

    If any of the above pre-conditions is not met, the inputs are considered invalid, in which
    case this function **might** raise an error.

    Args:
        plaquette_array: an array of indices referencing Plaquette instances in the
            `plaquettes` argument.
        plaquettes: description of the computation that should happen at
            different time-slices of the quantum error correction experiment (or
            at least part of it). If provided as a dictionary, plaquettes should be
            1-indexed (i.e., ``0 not in plaquettes`` should be ``True``).
        increments: the displacement between each plaquette origin.

    Returns:
        a cirq.Circuit instance implementing the (part of) quantum error
        correction experiment represented by the provided inputs.

    Raises:
        TQECException: if any index in `plaquette_array` is not correctly associated to a
            plaquette in `plaquettes` or if `plaquettes` is provided as a dictionary and
            `0 in plaquettes`.
    """
    # Check that the user gave enough plaquettes.
    indices = numpy.unique(plaquette_array)
    # Remove the first 0 entry in indices if present
    if indices[0] == 0:
        indices = indices[1:]
    expected_plaquettes_number = len(indices)
    if (
        not isinstance(plaquettes, defaultdict)
        and len(plaquettes) != expected_plaquettes_number
    ):
        raise TQECException(
            f"{len(plaquettes)} plaquettes have been provided, but "
            f"{expected_plaquettes_number} were expected."
        )
    if isinstance(plaquettes, ty.Mapping) and 0 in plaquettes:
        raise TQECException(
            "If using a dictionary, the input plaquettes parameter should not "
            f"contain the entry 0. Found a value ({plaquettes[0]}) at entry 0."
        )

    # If plaquettes are given as a list, make that a dict to simplify the following operations
    if isinstance(plaquettes, list):
        plaquettes = {i + 1: plaquette for i, plaquette in enumerate(plaquettes)}

    # Plaquettes indices are starting at 1 in template_plaquettes. To avoid
    # offsets in the following code, we add an empty circuit at position 0.
    plaquette_circuits = {0: ScheduledCircuit(cirq.Circuit())} | {
        i: plaquettes[i].circuit for i in indices
    }

    # Generate the ScheduledCircuit instances for each plaquette instantiation
    all_scheduled_circuits: list[ScheduledCircuit] = []
    plaquette_index: int
    for row_index, line in enumerate(plaquette_array):
        for column_index, plaquette_index in enumerate(line):
            if plaquette_index != 0:
                scheduled_circuit = deepcopy(plaquette_circuits[plaquette_index])
                offset = Displacement(
                    column_index * increments.x, row_index * increments.y
                )
                plaquette = plaquettes[plaquette_index]
                qubit_map = _create_mapping(plaquette, scheduled_circuit, offset)
                scheduled_circuit.map_to_qubits(qubit_map, inplace=True)
                all_scheduled_circuits.append(scheduled_circuit)

    # Merge everything!
    return merge_scheduled_circuits(all_scheduled_circuits)


def _create_mapping(
    plaquette: Plaquette, scheduled_circuit: ScheduledCircuit, offset: Displacement
) -> dict[cirq.GridQubit, cirq.GridQubit]:
    origin = plaquette.origin

    qubit_map = {
        # GridQubit are indexed as (row, col), so (y, x)
        # Qubits are given relative to an origin, so we need to add the offset
        qubit: qubit + (offset.y, offset.x) + (origin.y, origin.x)
        for qubit in scheduled_circuit.mappable_qubits
    }
    return qubit_map
