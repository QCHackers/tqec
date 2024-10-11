from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy
import stim

from tqec.circuit.measurement import (
    MULTIPLE_QUBIT_MEASUREMENT_INSTRUCTION_NAMES,
    SINGLE_QUBIT_MEASUREMENT_INSTRUCTION_NAMES,
)
from tqec.circuit.qubit import GridQubit
from tqec.circuit.qubit_map import QubitMap
from tqec.circuit.schedule import ScheduledCircuit
from tqec.exceptions import TQECException


@dataclass(frozen=True)
class MeasurementRecordsMap:
    """A mapping from measurements appearing in a circuit and their record offsets.

    This class stores record offsets which are, by essence, relative to a certain
    position in a circuit. This means that this class and the measurement offsets
    it stores are meaningless without knowledge about the circuit containing the
    represented measurements and the position(s) in the circuit at which the
    instance at hand is valid.

    Raises:
        TQECException: if at least one of the provided measurement record offsets
            is non-negative (`>=0`).
        TQECException: if, for any of the provided qubits, the provided offsets
            are not sorted.
        TQECException: if any measurement offset is duplicated.
    """

    mapping: dict[GridQubit, list[int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        all_measurement_records_indices: list[int] = []
        for qubit, measurement_record_offsets in self.mapping.items():
            # Check that the provided measurement record offsets are negative.
            positive_offsets = [
                offset for offset in measurement_record_offsets if offset >= 0
            ]
            if positive_offsets:
                raise TQECException(
                    "Invalid mapping from qubit offsets to measurement record "
                    f"offsets. Found positive offsets ({positive_offsets}) for "
                    f"qubit {qubit}."
                )
            # Check that measurement record offsets are sorted
            if measurement_record_offsets != sorted(measurement_record_offsets):
                raise TQECException(
                    "Got measurement record offsets that are not in sorted "
                    f"order: {measurement_record_offsets}. This is not supported."
                )
            all_measurement_records_indices.extend(measurement_record_offsets)
        # Check that a given measurement record offset only appears once.
        deduplicated_indices = numpy.unique(all_measurement_records_indices)
        if len(deduplicated_indices) != len(all_measurement_records_indices):
            raise TQECException(
                "At least one measurement record offset has been found twice "
                "in the provided offsets."
            )

    @staticmethod
    def from_scheduled_circuit(circuit: ScheduledCircuit) -> MeasurementRecordsMap:
        """Build a :class:`MeasurementMap` from a scheduled circuit.

        Args:
            circuit: circuit containing the measurements to map.

        Raises:
            TQECException: if the provided `circuit` contains a `REPEAT` block.
            TQECException: if the provided `circuit` contains an unsupported
                measurement instruction. Currently, this method supports all
                single-qubit measurement instructions (see the value of
                `SINGLE_QUBIT_MEASUREMENT_INSTRUCTION_NAMES`).
            TQECException: if one of the measurement counted in
                `circuit.num_measurements` was not processed (this should never
                raise, but the post-condition is easy to check so this method
                performs the check just in case).

        Returns:
            a :class:`MeasurementMap` linking measurements in the provided
            `circuit` to their offset.
        """
        return MeasurementRecordsMap.from_circuit(
            circuit.get_circuit(include_qubit_coords=False), circuit.qubit_map
        )

    @staticmethod
    def from_circuit(
        circuit: stim.Circuit, qubit_map: QubitMap | None = None
    ) -> MeasurementRecordsMap:
        """Build a :class:`MeasurementMap` from a circuit.

        Args:
            circuit: circuit containing the measurements to map.
            qubit_map: qubit map of the provided circuit. If `None`, the
                qubit map is computed from the provided circuit. Default to
                `None`.
        Raises:
            TQECException: if the provided `circuit` contains a `REPEAT` block.
            TQECException: if the provided `circuit` contains an unsupported
                measurement instruction. Currently, this method supports all
                single-qubit measurement instructions (see the value of
                `SINGLE_QUBIT_MEASUREMENT_INSTRUCTION_NAMES`).
            TQECException: if one of the measurement counted in
                `circuit.num_measurements` was not processed (this should never
                raise, but the post-condition is easy to check so this method
                performs the check just in case).

        Returns:
            a :class:`MeasurementMap` linking measurements in the provided
            `circuit` to their offset.
        """
        # We iterate the circuit in forward order, which means that the first
        # measurement we will encounter will have a record offset of
        # `-circuit.num_measurements`. Iterating in this order also allows to
        # ensure by construction that the measurement record offsets will be in
        # sorted order.
        current_measurement_record = -circuit.num_measurements
        if qubit_map is None:
            qubit_map = QubitMap.from_circuit(circuit)
        measurement_records: dict[GridQubit, list[int]] = {}
        for instruction in circuit:
            if isinstance(instruction, stim.CircuitRepeatBlock):
                raise TQECException(
                    "Found a REPEAT instruction. This is not supported for the moment."
                )
            if instruction.name in MULTIPLE_QUBIT_MEASUREMENT_INSTRUCTION_NAMES:
                raise TQECException(
                    f"Found a non-supported measurement instruction: {instruction}"
                )
            if instruction.name in SINGLE_QUBIT_MEASUREMENT_INSTRUCTION_NAMES:
                for (qi,) in instruction.target_groups():
                    qubit = qubit_map.i2q[qi.value]
                    measurement_records.setdefault(qubit, []).append(
                        current_measurement_record
                    )
                    current_measurement_record += 1
        if current_measurement_record != 0:
            raise TQECException(
                "Failed post-condition check. Expected a final measurement record of "
                f"-1 but got {current_measurement_record - 1}. Did we miss a "
                f"measurement? Circuit:\n{circuit}"
            )
        return MeasurementRecordsMap(measurement_records)

    # Explicitly returns a Sequence to show that the returned value is read-only.
    def __getitem__(self, qubit: GridQubit) -> Sequence[int]:
        return self.mapping[qubit]

    def __contains__(self, qubit: GridQubit) -> bool:
        return qubit in self.mapping