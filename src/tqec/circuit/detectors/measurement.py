from dataclasses import dataclass


@dataclass(frozen=True)
class MeasurementLocation:
    qubit: int
