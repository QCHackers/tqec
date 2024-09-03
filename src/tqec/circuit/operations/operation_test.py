import cirq
import pytest

from tqec.circuit.operations.measurement import Measurement
from tqec.circuit.operations.operation import (
    Detector,
    MeasurementsRecord,
    Observable,
    ShiftCoords,
    make_detector,
    make_observable,
    make_shift_coords,
)
from tqec.exceptions import TQECException

_qubits_examples = [
    cirq.GridQubit(0, 0),
    cirq.GridQubit(2, 2),
    cirq.GridQubit(-1, 1),
    cirq.GridQubit(-10, -3),
    cirq.GridQubit(-1, 0),
]


def test_empty_shift_coords() -> None:
    with pytest.raises(
        TQECException,
        match="The number of shift coordinates should be between 1 and 16, but got 0.",
    ):
        make_shift_coords()


def test_shift_coords() -> None:
    sc_tagged = make_shift_coords(-1, 0, 18, 2**57)
    assert isinstance(sc_tagged.untagged, ShiftCoords)
    sc_untagged: ShiftCoords = sc_tagged.untagged
    assert sc_untagged.shifts == (-1, 0, 18, 2**57)


@pytest.mark.parametrize("origin", _qubits_examples)
def test_empty_detector(origin: cirq.GridQubit) -> None:
    detector_tagged = make_detector([], coordinates=(0.0, 0.0, 0.0))
    assert isinstance(detector_tagged.untagged, Detector)
    detector_untagged: Detector = detector_tagged.untagged
    assert detector_untagged.coordinates == (0.0, 0.0, 0.0)


def test_detector_repeated_measurement() -> None:
    measurements: list[Measurement] = [
        Measurement(cirq.GridQubit(0, 0), -1),
        Measurement(cirq.GridQubit(0, 0), -1),
    ]
    with pytest.raises(TQECException):
        # Duplicated relative measurements
        make_detector(measurements, coordinates=(0.0, 0.0, 0.0))


def test_detector_with_measurement() -> None:
    measurements: list[Measurement] = [
        Measurement(cirq.GridQubit(0, 0), -1),
        Measurement(cirq.GridQubit(0, 0), -2),
    ]
    make_detector(measurements, coordinates=(0.0, 0.0, 0.0))


def test_detector_negative_time_coordinate() -> None:
    measurements: list[Measurement] = [
        Measurement(cirq.GridQubit(0, 0), -1),
        Measurement(cirq.GridQubit(0, 0), -2),
    ]
    with pytest.raises(TQECException):
        make_detector(measurements, coordinates=(0.0, 0.0, -1.0))


def test_empty_observable() -> None:
    observable_tagged = make_observable([], observable_index=0)
    assert isinstance(observable_tagged.untagged, Observable)
    observable_untagged: Observable = observable_tagged.untagged
    assert observable_untagged.index == 0


def test_observable_with_measurement() -> None:
    measurements: list[Measurement] = [
        Measurement(cirq.GridQubit(0, 0), -1),
        Measurement(cirq.GridQubit(0, 0), -2),
    ]
    make_observable(measurements, observable_index=0)


def test_observable_negative_index() -> None:
    measurements: list[Measurement] = [
        Measurement(cirq.GridQubit(0, 0), -1),
        Measurement(cirq.GridQubit(0, 0), -2),
    ]
    with pytest.raises(TQECException):
        make_observable(measurements, observable_index=-1)


def test_measurement_record_duplicated_measurement_data() -> None:
    qubit = cirq.GridQubit(0, 0)
    with pytest.raises(TQECException):
        MeasurementsRecord(
            [
                Measurement(qubit, -1),
                Measurement(qubit, -2),
                Measurement(qubit, -1),
            ],
        )
