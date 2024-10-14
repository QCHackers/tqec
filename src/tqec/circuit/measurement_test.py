import pytest
import stim

from tqec.circuit.measurement import (
    Measurement,
    RepeatedMeasurement,
    get_measurements_from_circuit,
)
from tqec.circuit.qubit import GridQubit
from tqec.circuit.qubit_map import QubitMap
from tqec.circuit.schedule import ScheduledCircuit
from tqec.exceptions import TQECException
from tqec.interval import Interval
from tqec.position import Displacement

_grid_qubits: list[GridQubit] = [GridQubit(0, 0), GridQubit(-1, -1)]


@pytest.mark.parametrize("qubit", _grid_qubits)
def test_measurement_construction(qubit: GridQubit) -> None:
    Measurement(qubit, -1)
    Measurement(qubit, -10)
    with pytest.raises(TQECException, match="^Measurement.offset should be negative.$"):
        Measurement(qubit, 0)
    with pytest.raises(TQECException, match="^Measurement.offset should be negative.$"):
        Measurement(qubit, 10)


@pytest.mark.parametrize("qubit", _grid_qubits)
def test_repeated_measurement_construction(qubit: GridQubit) -> None:
    RepeatedMeasurement(
        qubit, Interval(-10, -1, start_excluded=False, end_excluded=False)
    )
    RepeatedMeasurement(
        qubit, Interval(-10, 0, start_excluded=False, end_excluded=True)
    )
    with pytest.raises(
        TQECException,
        match=(
            "^Measurement.offsets should be an Interval "
            "containing only strictly negative values.$"
        ),
    ):
        RepeatedMeasurement(
            qubit, Interval(-10, 0, start_excluded=False, end_excluded=False)
        )
    with pytest.raises(
        TQECException,
        match=(
            "^Measurement.offsets should be an Interval "
            "containing only strictly negative values.$"
        ),
    ):
        RepeatedMeasurement(
            qubit, Interval(1, 10, start_excluded=False, end_excluded=False)
        )


@pytest.mark.parametrize("qubit", _grid_qubits)
def test_measurement_offset(qubit: GridQubit) -> None:
    assert Measurement(qubit, -1).offset_spatially_by(0, 0) == Measurement(qubit, -1)
    assert Measurement(qubit, -1).offset_spatially_by(1, 0) == Measurement(
        qubit + Displacement(1, 0), -1
    )
    assert Measurement(qubit, -1).offset_spatially_by(-3, 12) == Measurement(
        qubit + Displacement(-3, 12), -1
    )
    assert Measurement(qubit, -2).offset_spatially_by(0, 0) == Measurement(qubit, -2)

    assert Measurement(qubit, -1).offset_temporally_by(-12) == Measurement(qubit, -13)

    with pytest.raises(TQECException, match="^Measurement.offset should be negative.$"):
        Measurement(qubit, -1).offset_temporally_by(1)


@pytest.mark.parametrize("qubit", _grid_qubits)
def test_repeated_measurement_offset(qubit: GridQubit) -> None:
    interval = Interval(-10, -1, start_excluded=False, end_excluded=False)
    assert RepeatedMeasurement(qubit, interval).offset_spatially_by(
        0, 0
    ) == RepeatedMeasurement(qubit, interval)
    assert RepeatedMeasurement(qubit, interval).offset_spatially_by(
        0, 1
    ) == RepeatedMeasurement(qubit + Displacement(0, 1), interval)
    assert RepeatedMeasurement(qubit, interval).offset_spatially_by(
        3, -6
    ) == RepeatedMeasurement(qubit + Displacement(3, -6), interval)

    assert RepeatedMeasurement(qubit, interval).offset_temporally_by(
        -10
    ) == RepeatedMeasurement(
        qubit, Interval(-20, -11, start_excluded=False, end_excluded=False)
    )
    with pytest.raises(
        TQECException,
        match=(
            "^Measurement.offsets should be an Interval "
            "containing only strictly negative values.$"
        ),
    ):
        RepeatedMeasurement(qubit, interval).offset_temporally_by(1)


def test_measurement_map_qubit() -> None:
    qubit_map = {q: q + Displacement(3, 8) for q in _grid_qubits}

    for qubit in _grid_qubits:
        assert Measurement(qubit, -1).map_qubit(qubit_map) == Measurement(
            qubit_map[qubit], -1
        )


def test_repeated_measurement_map_qubit() -> None:
    interval = Interval(-10, -1, start_excluded=False, end_excluded=False)
    qubit_map = {q: q + Displacement(3, 8) for q in _grid_qubits}

    for qubit in _grid_qubits:
        assert RepeatedMeasurement(qubit, interval).map_qubit(
            qubit_map
        ) == RepeatedMeasurement(qubit_map[qubit], interval)


def test_repeated_measurement_measurements() -> None:
    interval = Interval(-10, -1, start_excluded=False, end_excluded=False)
    qubit = GridQubit(0, 0)
    assert RepeatedMeasurement(qubit, interval).measurements() == [
        Measurement(qubit, i) for i in range(-10, 0)
    ]


def test_get_measurements_from_circuit() -> None:
    circuit = ScheduledCircuit.from_circuit(
        stim.Circuit("H 0\nM 1 2\nTICK\nMX 2 3"),
        qubit_map=QubitMap({i: GridQubit(i, i) for i in range(4)}),
    )
    measurements = get_measurements_from_circuit(
        circuit.get_circuit(include_qubit_coords=True)
    )
    assert frozenset(measurements) == frozenset(
        [
            Measurement(GridQubit(1, 1), -1),
            Measurement(GridQubit(2, 2), -2),
            Measurement(GridQubit(2, 2), -1),
            Measurement(GridQubit(3, 3), -1),
        ]
    )
