from dataclasses import dataclass

import numpy

from tqec.circuit.measurement import Measurement


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
