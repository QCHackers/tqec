from dataclasses import dataclass

from tqec.exceptions import TQECException


@dataclass(frozen=True)
class RelativeMeasurementLocation:
    """Represents a unique measurement with an offset.

    Measurements are represented with the same method as stim: by a negative
    offset. This means that instances of this class have no meaning if they
    are not associated with a precise point in the circuit, but this also
    means that they can represent measurements without the need for global
    information.
    """

    offset: int

    def __post_init__(self):
        if self.offset >= 0:
            raise TQECException(
                "Relative measurement offsets should be strictly negative."
            )


def get_relative_measurement_index(
    all_measured_qubits: list[int], measured_qubit: int
) -> RelativeMeasurementLocation:
    return RelativeMeasurementLocation(
        all_measured_qubits.index(measured_qubit) - len(all_measured_qubits)
    )
