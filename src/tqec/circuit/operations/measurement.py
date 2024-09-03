from __future__ import annotations

import typing
from dataclasses import dataclass

import cirq

from tqec.exceptions import TQECException
from tqec.templates.interval import Interval, Rplus_interval


@dataclass(frozen=True)
class Measurement:
    """A unique representation for each measurement in a quantum circuit.

    This class aims at being able to represent measurements in a quantum circuit
    in a unique and easily usable way.

    Note:
        This is not a global representation as the `offset` is always
        relative to the end of the quantum circuit considered.

    Attributes:
        qubit: qubit on which the represented measurement is performed.
        offset: negative offset representing the number of measurements
            performed on the provided qubit after the represented measurement.
            A value of `-1` means that the represented measurement is the
            last one applied on `qubit`.

    Raises:
        TQECException: if the provided `offset` is not strictly negative.
    """

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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.qubit}, {self.offset})"

    def map_qubit(
        self, qubit_map: typing.Mapping[cirq.GridQubit, cirq.GridQubit]
    ) -> Measurement:
        return Measurement(qubit_map[self.qubit], self.offset)


@dataclass(frozen=True)
class RepeatedMeasurement:
    """A unique representation for a repeated measurement in a quantum circuit.

    This class aims at being able to represent a repeated measurement in a
    quantum circuit in a unique and easily usable way.
    Repeated measurements can be found when a :class:`stim.CircuitRepeatBlock`
    contains measurements.

    Note:
        This is not a global representation as the `offsets` is always
        relative to the end of the quantum circuit considered.

    Attributes:
        qubit: qubit on which the represented repeated measurement is performed.
        offsets: an interval only containing negative offsets representing the
            number of measurements performed on the provided qubit after the
            represented measurement.
            A value of `-1` means that the represented measurement is the
            last one applied on `qubit`.

    Raises:
        TQECException: if the provided `offsetd` contains positive entries.
    """

    qubit: cirq.GridQubit
    offsets: Interval

    def __post_init__(self) -> None:
        if not self.offsets.intersection(Rplus_interval).is_empty():
            raise TQECException(
                "Measurement.offsets should be an Interval "
                "containing only strictly negative values."
            )

    def offset_spatially_by(self, x: int, y: int) -> RepeatedMeasurement:
        return RepeatedMeasurement(self.qubit + (y, x), self.offsets)

    def offset_temporally_by(self, t: int) -> RepeatedMeasurement:
        return RepeatedMeasurement(self.qubit, self.offsets + t)

    def measurements(self) -> list[Measurement]:
        return [
            Measurement(self.qubit, offset) for offset in self.offsets.iter_integers()
        ]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.qubit}, {self.offsets})"
