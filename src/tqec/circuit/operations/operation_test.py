import cirq
import pytest

from tqec.circuit.operations.operation import (
    Detector,
    Observable,
    RelativeMeasurementData,
    RelativeMeasurementsRecord,
    ShiftCoords,
    make_detector,
    make_observable,
    make_shift_coords,
    observable_qubits_from_template,
)
from tqec.exceptions import TQECException
from tqec.plaquette.library import XXXXMemoryPlaquette, ZZZZMemoryPlaquette
from tqec.templates import RawRectangleTemplate

_qubits_examples = [
    cirq.GridQubit(0, 0),
    cirq.GridQubit(2, 2),
    cirq.GridQubit(-1, 1),
    cirq.GridQubit(-10, -3),
    cirq.GridQubit(-1, 0),
]


def test_empty_shift_coords():
    with pytest.raises(
        TQECException,
        match="The number of shift coordinates should be between 1 and 16, but got 0.",
    ):
        make_shift_coords()


def test_shift_coords():
    sc_tagged = make_shift_coords(-1, 0, 18, 2**57)
    assert isinstance(sc_tagged.untagged, ShiftCoords)
    sc_untagged: ShiftCoords = sc_tagged.untagged
    assert sc_untagged.shifts == (-1, 0, 18, 2**57)


@pytest.mark.parametrize("origin", _qubits_examples)
def test_empty_detector(origin):
    detector_tagged = make_detector(origin, [], time_coordinate=0)
    assert isinstance(detector_tagged.untagged, Detector)
    detector_untagged: Detector = detector_tagged.untagged
    assert detector_untagged.origin == origin
    assert detector_untagged.coordinates == (origin.row, origin.col, 0)


def test_detector_repeated_relative_measurement():
    origin = cirq.GridQubit(0, 0)
    relative_measurements: list[tuple[cirq.GridQubit, int]] = [
        (cirq.GridQubit(0, 0), -1),
        (cirq.GridQubit(0, 0), -1),
    ]
    with pytest.raises(TQECException):
        # Duplicated relative measurements
        make_detector(origin, relative_measurements, time_coordinate=0)


def test_detector_with_relative_measurement():
    origin = cirq.GridQubit(0, 0)
    relative_measurements: list[tuple[cirq.GridQubit, int]] = [
        (cirq.GridQubit(0, 0), -1),
        (cirq.GridQubit(0, 0), -2),
    ]
    make_detector(origin, relative_measurements, time_coordinate=0)


def test_detector_negative_time_coordinate():
    origin = cirq.GridQubit(0, 0)
    relative_measurements: list[tuple[cirq.GridQubit, int]] = [
        (cirq.GridQubit(0, 0), -1),
        (cirq.GridQubit(0, 0), -2),
    ]
    with pytest.raises(TQECException):
        make_detector(origin, relative_measurements, time_coordinate=-1)


@pytest.mark.parametrize("origin", _qubits_examples)
def test_empty_observable(origin):
    observable_tagged = make_observable(origin, [], observable_index=0)
    assert isinstance(observable_tagged.untagged, Observable)
    observable_untagged: Observable = observable_tagged.untagged
    assert observable_untagged.origin == origin
    assert observable_untagged.index == 0


def test_observable_with_relative_measurement():
    origin = cirq.GridQubit(0, 0)
    relative_measurements: list[tuple[cirq.GridQubit, int]] = [
        (cirq.GridQubit(0, 0), -1),
        (cirq.GridQubit(0, 0), -2),
    ]
    make_observable(origin, relative_measurements, observable_index=0)


def test_observable_negative_index():
    origin = cirq.GridQubit(0, 0)
    relative_measurements: list[tuple[cirq.GridQubit, int]] = [
        (cirq.GridQubit(0, 0), -1),
        (cirq.GridQubit(0, 0), -2),
    ]
    with pytest.raises(TQECException):
        make_observable(origin, relative_measurements, observable_index=-1)


def test_relative_measure_data_negative_index():
    with pytest.raises(TQECException):
        RelativeMeasurementData(cirq.GridQubit(0, 0), 0)
    with pytest.raises(TQECException):
        RelativeMeasurementData(cirq.GridQubit(0, 0), 1)


def test_relative_measurement_record_duplicated_measurement_data():
    origin = cirq.GridQubit(0, 0)
    with pytest.raises(TQECException):
        RelativeMeasurementsRecord(
            origin,
            [
                RelativeMeasurementData(origin, -1),
                RelativeMeasurementData(origin, -2),
                RelativeMeasurementData(origin, -1),
            ],
        )


def test_raw_rectangle_default_observable_qubits():
    template = RawRectangleTemplate(
        [
            [0, 1, 0, 1],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [1, 0, 1, 0],
        ]
    )
    plaquettes = [
        XXXXMemoryPlaquette([1, 2, 3, 4, 5, 6, 7, 8]),
        ZZZZMemoryPlaquette([1, 3, 4, 5, 6, 8]),
    ]
    obs = observable_qubits_from_template(template, plaquettes)
    result = [
        (cirq.GridQubit(3, -1), 0),
        (cirq.GridQubit(3, 1), 0),
        (cirq.GridQubit(3, 3), 0),
        (cirq.GridQubit(3, 5), 0),
        (cirq.GridQubit(3, 7), 0),
    ]
    assert sorted(obs, key=lambda t: t[0].col == result)
