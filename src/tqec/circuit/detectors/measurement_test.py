import pytest
from tqec.circuit.detectors.measurement import (
    RelativeMeasurementLocation,
    get_relative_measurement_index,
)
from tqec.exceptions import TQECException


def test_initialisation() -> None:
    RelativeMeasurementLocation(-1, 1)

    with pytest.raises(
        TQECException,
        match=r"^Relative measurement offsets should be strictly negative\.$",
    ):
        RelativeMeasurementLocation(0, 1)
    with pytest.raises(
        TQECException,
        match=r"^Relative measurement offsets should be strictly negative\.$",
    ):
        RelativeMeasurementLocation(1, 1)


def test_offset_by() -> None:
    rml = RelativeMeasurementLocation(-1, 1)
    assert rml.offset_by(-19) == RelativeMeasurementLocation(-20, 1)
    with pytest.raises(
        TQECException,
        match=r"^Relative measurement offsets should be strictly negative\.$",
    ):
        rml.offset_by(1)


def test_get_relative_measurement_index() -> None:
    all_measured_qubits = list(range(10))
    for qubit in all_measured_qubits:
        rml = get_relative_measurement_index(all_measured_qubits, qubit)
        assert rml.qubit_index == qubit
        assert rml.offset == qubit - len(all_measured_qubits)
