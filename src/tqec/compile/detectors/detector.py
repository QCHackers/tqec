"""Defines :class:`Detector` to represent detectors."""

from __future__ import annotations

from dataclasses import dataclass

import numpy
import stim

from tqec.circuit.measurement import Measurement
from tqec.circuit.measurement_map import MeasurementRecordsMap
from tqec.exceptions import TQECException


@dataclass(frozen=True)
class Detector:
    """Represent a detector as a set of measurements and optional coordinates."""

    measurements: frozenset[Measurement]
    coordinates: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.measurements:
            raise TQECException("Trying to create a detector without any measurement.")
        if len(self.coordinates) < 2:
            raise TQECException(
                "Coordinates should at least provide 2 spatial dimensions. "
                f"The provided  coordinates {self.coordinates} only contain "
                f"{len(self.coordinates)} dimensions."
            )

    def __hash__(self) -> int:
        return hash(self.measurements)

    def __eq__(self, rhs: object) -> bool:
        return (
            isinstance(rhs, Detector)
            and self.measurements == rhs.measurements
            and numpy.allclose(self.coordinates, rhs.coordinates)
        )

    def __str__(self) -> str:
        coordinates_str = "(" + ",".join(f"{c:.2f}" for c in self.coordinates) + ")"
        measurements_str = "{" + ",".join(map(str, self.measurements)) + "}"
        return f"D{coordinates_str}{measurements_str}"

    def to_instruction(
        self, measurement_records_map: MeasurementRecordsMap
    ) -> stim.CircuitInstruction:
        """Return the `stim.CircuitInstruction` instance representing the
        detector stored in `self`.

        Args:
            measurement_records_map: a map from qubits and qubit-local
                measurement offsets to global measurement offsets.

        Raises:
            TQECException: if any of the measurements stored in `self` is
                performed on a qubit that is not in the provided
                `measurement_records_map`.
            KeyError: if any of the qubit-local measurement offsets stored in
                `self` is not present in the provided `measurement_records_map`.

        Returns:
            the `DETECTOR` instruction representing `self`. Note that the
            instruction has the same validity region as the provided
            `measurement_records_map`.
        """
        measurement_records: list[stim.GateTarget] = []
        for measurement in self.measurements:
            if measurement.qubit not in measurement_records_map:
                raise TQECException(
                    f"Trying to get measurement record for {measurement.qubit} "
                    "but qubit is not in the measurement record map."
                )
            measurement_records.append(
                stim.target_rec(
                    measurement_records_map[measurement.qubit][measurement.offset]
                )
            )
        return stim.CircuitInstruction(
            "DETECTOR", measurement_records, self.coordinates
        )

    def offset_spatially_by(self, x: int, y: int) -> Detector:
        """Offset the coordinates and all the qubits involved in `self`.

        Args:
            x: offset in the first spatial dimension.
            y: offset in the second spatial dimension.

        Returns:
            a new detector that has been spatially offset by the provided `x`
            and `y` offsets.
        """

        return Detector(
            frozenset(m.offset_spatially_by(x, y) for m in self.measurements),
            (self.coordinates[0] + x, self.coordinates[1] + y, *self.coordinates[2:]),
        )
