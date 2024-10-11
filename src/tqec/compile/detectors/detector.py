from __future__ import annotations

from dataclasses import dataclass

import numpy
import stim

from tqec.circuit.measurement import Measurement
from tqec.circuit.measurement_map import MeasurementRecordsMap
from tqec.exceptions import TQECException


@dataclass(frozen=True)
class Detector:
    measurements: frozenset[Measurement]
    coordinates: tuple[float, ...]

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
        if len(self.coordinates) < 2:
            raise TQECException(
                f"Cannot offset spatially the coordinates {self.coordinates} "
                "because at least one spatial dimension is missing (2 dimensions "
                "are expected)."
            )
        return Detector(
            frozenset(m.offset_spatially_by(x, y) for m in self.measurements),
            (self.coordinates[0] + x, self.coordinates[1] + y, *self.coordinates[2:]),
        )
