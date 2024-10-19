"""Defines :meth:`generate_circuit`, one of the core method of the `tqec`
package.

This module defines two of core methods of the `tqec` package:

- :meth:`generate_circuit` that is the most convenient method for external users.
- :meth:`generate_circuit_from_instantiation` that gives more freedom to the
  user (and is used internally by :meth:`generate_circuit`) at the expense of
  often less convenient inputs.

Both of these methods are used to generate the `stim.Circuit` instance
representing **one** time slice (often equivalent to "one QEC round"). Users are
expected to call these methods several times and concatenate the output
`stim.Circuit` instances in time to obtain a full QEC implementation.

Note that these methods do not work with `REPEAT` instructions.
"""

from __future__ import annotations

from copy import deepcopy

import numpy
import numpy.typing as npt

from tqec.circuit.qubit import GridQubit
from tqec.circuit.schedule import ScheduledCircuit, merge_scheduled_circuits
from tqec.exceptions import TQECException
from tqec.plaquette.plaquette import Plaquette, Plaquettes
from tqec.position import Displacement
from tqec.templates.base import Template


def generate_circuit(
    template: Template, k: int, plaquettes: Plaquettes
) -> ScheduledCircuit:
    """Generate a quantum circuit from a template and its plaquettes.

    This is one of the core methods of the `tqec` package. It generates a
    quantum circuit from the description of the template that should be
    implemented as well as the plaquettes that should be used to instantiate the
    provided template.

    This function requires that a few pre-conditions on the inputs are met:

    1. the number of plaquettes provided should match the number of plaquettes
       required by the provided template.
    2. all the provided plaquettes should be implemented on :class:`GridQubit`
       instances **only**.

    If any of the above pre-conditions is not met, the inputs are considered
    invalid, in which case this function **might** raise an error.

    Args:
        template: spatial description of the quantum error correction experiment
            we want to implement.
        k: scaling parameter used to instantiate the provided `template`.
        plaquettes: description of the computation that should happen at
            different time-slices of the quantum error correction experiment (or
            at least part of it).

    Returns:
        a `ScheduledCircuit` instance implementing the (part of) quantum error
        correction experiment represented by the provided inputs.

    Raises:
        TQECException: if `len(plaquettes) != template.expected_plaquettes_number`.
    """
    # instantiate the template with the appropriate plaquette indices.
    # Index 0 is "no plaquette" by convention and should not be included here.
    _indices = list(range(1, template.expected_plaquettes_number + 1))
    template_plaquettes = template.instantiate(k, _indices)
    increments = template.get_increments()

    return generate_circuit_from_instantiation(
        template_plaquettes, plaquettes, increments
    )


def generate_circuit_from_instantiation(
    plaquette_array: npt.NDArray[numpy.int_],
    plaquettes: Plaquettes,
    increments: Displacement,
) -> ScheduledCircuit:
    """Generate a quantum circuit from an array of plaquette indices and the
    associated plaquettes.

    This is one of the core methods of the `tqec` package. It generates a
    quantum circuit from a spatial description of where the plaquettes should be
    located as well as the actual plaquettes used.

    This function requires that a few pre-conditions on the inputs are met:

    1. the number of plaquettes provided should match the number of plaquettes
       required by the provided template.
    2. all the provided plaquettes should be implemented on :class:`GridQubit`
       instances **only**.

    If any of the above pre-conditions is not met, the inputs are considered
    invalid, in which case this function **might** raise an error.

    Args:
        plaquette_array: an array of indices referencing Plaquette instances in
            the `plaquettes` argument.
        plaquettes: description of the computation that should happen at
            different time-slices of the quantum error correction experiment (or
            at least part of it).
        increments: the displacement between each plaquette origin.

    Returns:
        a `ScheduledCircuit` instance implementing the (part of) quantum error
        correction experiment represented by the provided inputs.

    Raises:
        TQECException: if any index in `plaquette_array` is not correctly
            associated to a plaquette in `plaquettes`.
    """
    # Check that the user gave enough plaquettes.
    indices = numpy.unique(plaquette_array)
    # Remove the first 0 entry in indices if present
    if indices[0] == 0:
        indices = indices[1:]

    # Plaquettes indices are starting at 1 in template_plaquettes. To avoid
    # offsets in the following code, we add an empty circuit at position 0.
    plaquette_circuits = {0: ScheduledCircuit.empty()} | {
        i: plaquettes[i].circuit for i in indices
    }

    # Generate the ScheduledCircuit instances for each plaquette instantiation
    all_scheduled_circuits: list[ScheduledCircuit] = []
    plaquette_index: int
    additional_mergeable_instructions: set[str] = set()
    for row_index, line in enumerate(plaquette_array):
        for column_index, plaquette_index in enumerate(line):
            if plaquette_index != 0:
                # Warning: this is a reference to a shared circuit. It cannot be
                #          changed in-place!!
                scheduled_circuit = plaquette_circuits[plaquette_index]
                plaquette = plaquettes[plaquette_index]
                qubit_offset = Displacement(
                    plaquette.origin.x + column_index * increments.x,
                    plaquette.origin.y + row_index * increments.y,
                )
                mapped_scheduled_circuit = scheduled_circuit.map_to_qubits(
                    lambda q: q + qubit_offset, inplace=False
                )
                all_scheduled_circuits.append(mapped_scheduled_circuit)
                additional_mergeable_instructions |= plaquette.mergeable_instructions

    # Merge everything!
    return merge_scheduled_circuits(
        all_scheduled_circuits, additional_mergeable_instructions
    )
