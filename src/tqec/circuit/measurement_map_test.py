import re

import pytest
import stim

from tqec.circuit.measurement_map import MeasurementRecordsMap
from tqec.circuit.qubit import GridQubit
from tqec.circuit.qubit_map import QubitMap
from tqec.circuit.schedule import ScheduledCircuit
from tqec.exceptions import TQECException


def test_measurement_records_map_creation() -> None:
    MeasurementRecordsMap()
    MeasurementRecordsMap({})

    q = GridQubit(0, 0)
    MeasurementRecordsMap({q: []})
    MeasurementRecordsMap({q: [-2, -1]})

    with pytest.raises(
        TQECException,
        match="^Invalid mapping from qubit offsets to measurement record "
        f"offsets. Found positive offsets \\({re.escape(str([0]))}\\) for qubit "
        f"{re.escape(str(q))}.$",
    ):
        MeasurementRecordsMap({q: [-2, 0]})

    with pytest.raises(
        TQECException,
        match="^Got measurement record offsets that are not in sorted order.*",
    ):
        MeasurementRecordsMap({q: [-1, -2]})

    q2 = GridQubit(1, 1)
    with pytest.raises(
        TQECException,
        match="^At least one measurement record offset has been found twice "
        "in the provided offsets.$",
    ):
        MeasurementRecordsMap({q: [-1], q2: [-1]})


def test_measurement_records_map_from_circuit() -> None:
    qubit_map = QubitMap({i: GridQubit(i, i) for i in range(3)})
    rec_map = MeasurementRecordsMap.from_circuit(stim.Circuit("M 0 2 1"), qubit_map)
    assert rec_map[GridQubit(0, 0)][-1] == -3
    assert rec_map[GridQubit(2, 2)][-1] == -2
    assert rec_map[GridQubit(1, 1)][-1] == -1

    rec_map = MeasurementRecordsMap.from_circuit(
        qubit_map.to_circuit() + stim.Circuit("M 0 2 1")
    )
    assert rec_map[GridQubit(0, 0)][-1] == -3
    assert rec_map[GridQubit(2, 2)][-1] == -2
    assert rec_map[GridQubit(1, 1)][-1] == -1


def test_measurement_records_map_from_scheduled_circuit() -> None:
    qubit_map = QubitMap({i: GridQubit(i, i) for i in range(3)})
    circuit = stim.Circuit("M 0 2 1\nTICK\nMX 0 1 2")
    scheduled_circuit = ScheduledCircuit.from_circuit(
        circuit, schedule=0, qubit_map=qubit_map
    )

    rec_map = MeasurementRecordsMap.from_scheduled_circuit(scheduled_circuit)
    assert rec_map[GridQubit(0, 0)][-1] == -3
    assert rec_map[GridQubit(0, 0)][-2] == -6
    assert rec_map[GridQubit(2, 2)][-1] == -1
    assert rec_map[GridQubit(2, 2)][-2] == -5
    assert rec_map[GridQubit(1, 1)][-1] == -2
    assert rec_map[GridQubit(1, 1)][-2] == -4
