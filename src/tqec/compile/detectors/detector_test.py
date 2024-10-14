import pytest
import stim

from tqec.circuit.measurement import Measurement
from tqec.circuit.measurement_map import MeasurementRecordsMap
from tqec.circuit.qubit import GridQubit
from tqec.compile.detectors.detector import Detector
from tqec.exceptions import TQECException


@pytest.fixture(name="measurement")
def measurement_fixture() -> Measurement:
    return Measurement(GridQubit(0, 0), -1)


@pytest.fixture(name="mrecords_map")
def mrecords_map_fixture() -> MeasurementRecordsMap:
    return MeasurementRecordsMap({GridQubit(0, 0): [-1]})


def test_detector_creation(measurement: Measurement) -> None:
    with pytest.raises(
        TQECException, match="^Trying to create a detector without any measurement.$"
    ):
        Detector(frozenset(), tuple())
    with pytest.raises(
        TQECException,
        match="^Coordinates should at least provide 2 spatial dimensions.",
    ):
        Detector(frozenset([measurement]), tuple())
    with pytest.raises(
        TQECException,
        match="^Coordinates should at least provide 2 spatial dimensions.",
    ):
        Detector(frozenset([measurement]), (1,))

    Detector(frozenset([measurement]), (0, 3))


def test_detector_to_instruction(
    measurement: Measurement, mrecords_map: MeasurementRecordsMap
) -> None:
    detector = Detector(frozenset([measurement]), (1, 1))
    instruction = detector.to_instruction(mrecords_map)
    assert instruction.name == "DETECTOR"
    assert instruction.targets_copy() == [stim.target_rec(-1)]
    assert instruction.gate_args_copy() == [1, 1]

    empty_mrecords_map = MeasurementRecordsMap()
    with pytest.raises(TQECException):
        detector.to_instruction(empty_mrecords_map)


def test_detector_offset_spatially_by(measurement: Measurement) -> None:
    detector = Detector(frozenset([measurement]), (1, 1))
    offset_detector = detector.offset_spatially_by(45, -2)
    assert offset_detector.measurements == frozenset(
        [measurement.offset_spatially_by(45, -2)]
    )
    assert offset_detector.coordinates == (46, -1)
