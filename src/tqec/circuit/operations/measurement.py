from __future__ import annotations

from dataclasses import dataclass

import cirq

from tqec.exceptions import TQECException
from tqec.templates.interval import Interval


@dataclass(frozen=True)
class Measurement:
    qubit: cirq.GridQubit
    offset: int

    def __post_init__(self) -> None:
        if self.offset >= 0:
            raise TQECException("Measurement.offset should be negative.")

    def offset_spatially_by(self, x: int, y: int) -> Measurement:
        return Measurement(self.qubit + (y, x), self.offset)

    def offset_temporally_by(self, t: int) -> Measurement:
        return Measurement(self.qubit, self.offset + t)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Measurement):
            raise NotImplementedError(f"Cannot compare {type(self)} < {type(other)}.")
        if self.offset == other.offset:
            return self.qubit < other.qubit
        return self.offset < other.offset


@dataclass(frozen=True)
class RepeatedMeasurement:
    qubit: cirq.GridQubit
    offsets: Interval

    def offset_spatially_by(self, x: int, y: int) -> RepeatedMeasurement:
        return RepeatedMeasurement(self.qubit + (y, x), self.offsets)

    def offset_temporally_by(self, t: int) -> RepeatedMeasurement:
        return RepeatedMeasurement(self.qubit, self.offsets + t)

    def measurements(self) -> list[Measurement]:
        return [
            Measurement(self.qubit, offset) for offset in self.offsets.iter_integers()
        ]
