from typing import Literal

import cirq
import pytest

from tqec.circuit.operations.measurement_map import CircuitMeasurementMap, flatten
from tqec.exceptions import TQECException


@pytest.fixture
def empty_circuit() -> cirq.Circuit:
    return cirq.Circuit()


@pytest.fixture
def flat_circuit() -> cirq.Circuit:
    qubits = cirq.GridQubit.rect(10, 10)
    return cirq.Circuit(
        [cirq.H(q) for q in qubits],
        [cirq.CX(qubits[i], qubits[i + 1]) for i in range(0, 100, 2)],
        [cirq.M(q) for q in qubits],
    )


@pytest.fixture
def circuit_with_depth1_circuit_operation() -> cirq.Circuit:
    qubits = cirq.GridQubit.rect(10, 10)
    return cirq.Circuit(
        [cirq.H(q) for q in qubits],
        cirq.CircuitOperation(
            cirq.Circuit(
                [cirq.CX(qubits[i], qubits[i + 1]) for i in range(0, 100, 2)]
            ).freeze()
        ),
        [cirq.M(q) for q in qubits],
    )


@pytest.fixture
def circuit_with_depth2_circuit_operation() -> cirq.Circuit:
    qubits = cirq.GridQubit.rect(10, 10)
    return cirq.Circuit(
        cirq.CircuitOperation(
            cirq.Circuit(
                [cirq.H(q) for q in qubits],
                cirq.CircuitOperation(
                    cirq.Circuit(
                        [cirq.CX(qubits[i], qubits[i + 1]) for i in range(0, 100, 2)]
                    ).freeze()
                ),
                [cirq.M(q) for q in qubits],
            ).freeze()
        )
    )


@pytest.fixture
def circuit_with_depth1_repeated_circuit_operation() -> cirq.Circuit:
    qubits = cirq.GridQubit.rect(10, 10)
    return cirq.Circuit(
        [cirq.H(q) for q in qubits],
        cirq.CircuitOperation(
            cirq.Circuit(
                [cirq.CX(qubits[i], qubits[i + 1]) for i in range(0, 100, 2)]
            ).freeze()
        ).repeat(10),
        [cirq.M(q) for q in qubits],
    )


@pytest.fixture
def circuit_with_repeated_measurements() -> cirq.Circuit:
    qubits = cirq.GridQubit.rect(10, 10)
    return cirq.Circuit(
        *[cirq.Moment([cirq.M(q) for q in qubits]) for _ in range(10)],
    )


def test_flatten_empty_circuit(empty_circuit: cirq.Circuit) -> None:
    flattened_circuit = flatten(empty_circuit)
    assert flattened_circuit == empty_circuit


def test_flatten_flat_circuit(flat_circuit: cirq.Circuit) -> None:
    flattened_circuit = flatten(flat_circuit)
    assert flattened_circuit == flat_circuit


def test_flatten_depth1_circuit(
    circuit_with_depth1_circuit_operation: cirq.Circuit, flat_circuit: cirq.Circuit
) -> None:
    flattened_circuit = flatten(circuit_with_depth1_circuit_operation)
    assert flattened_circuit == flat_circuit


def test_flatten_depth2_circuit(
    circuit_with_depth2_circuit_operation: cirq.Circuit, flat_circuit: cirq.Circuit
) -> None:
    flattened_circuit = flatten(circuit_with_depth2_circuit_operation)
    assert flattened_circuit == flat_circuit


def test_flatten_depth1_repeated_circuit(
    circuit_with_depth1_repeated_circuit_operation: cirq.Circuit,
) -> None:
    flattened_circuit = flatten(circuit_with_depth1_repeated_circuit_operation)
    assert all(
        not isinstance(op, cirq.CircuitOperation)
        for op in flattened_circuit.all_operations()
    )
    # There should be 500 CX gates
    assert (
        sum(op._num_qubits_() == 2 for op in flattened_circuit.all_operations()) == 500
    )


def test_measurement_map_empty_initialisation(empty_circuit: cirq.Circuit) -> None:
    CircuitMeasurementMap(empty_circuit)


def test_measurement_map_flat_initialisation(flat_circuit: cirq.Circuit) -> None:
    CircuitMeasurementMap(flat_circuit)


def test_measurement_map_depth1_initialisation(
    circuit_with_depth1_circuit_operation: cirq.Circuit,
) -> None:
    CircuitMeasurementMap(circuit_with_depth1_circuit_operation)


def test_measurement_map_depth2_initialisation(
    circuit_with_depth2_circuit_operation: cirq.Circuit,
) -> None:
    CircuitMeasurementMap(circuit_with_depth2_circuit_operation)


def test_measurement_map_depth1_repeated_initialisation(
    circuit_with_depth1_repeated_circuit_operation: cirq.Circuit,
) -> None:
    CircuitMeasurementMap(circuit_with_depth1_repeated_circuit_operation)


def test_measurement_map_lot_of_measurements_initialisation(
    circuit_with_repeated_measurements: cirq.Circuit,
) -> None:
    CircuitMeasurementMap(circuit_with_repeated_measurements)


def test_measurement_map_get_measurement_relative_offset_raises_on_positive_offset(
    empty_circuit: cirq.Circuit,
) -> None:
    mmap = CircuitMeasurementMap(empty_circuit)
    qubit = cirq.GridQubit(0, 0)
    with pytest.raises(TQECException):
        mmap.get_measurement_relative_offset(1, qubit, 0)
    with pytest.raises(TQECException):
        mmap.get_measurement_relative_offset(1, qubit, 10)


def test_measurement_map_get_measurement_relative_offset_raises_on_invalid_moment(
    flat_circuit: cirq.Circuit,
) -> None:
    mmap = CircuitMeasurementMap(flat_circuit)
    qubit = cirq.GridQubit(0, 0)
    with pytest.raises(TQECException):
        mmap.get_measurement_relative_offset(-10, qubit, -1)
    with pytest.raises(TQECException):
        mmap.get_measurement_relative_offset(-1, qubit, -1)
    with pytest.raises(TQECException):
        mmap.get_measurement_relative_offset(3, qubit, -1)
    with pytest.raises(TQECException):
        mmap.get_measurement_relative_offset(10, qubit, -1)


@pytest.mark.parametrize(
    "circuit_fixture",
    [
        "flat_circuit",
        "circuit_with_depth1_circuit_operation",
        "circuit_with_depth2_circuit_operation",
    ],
)
def test_measurement_map_get_measurement_relative_offset(
    circuit_fixture: Literal["flat_circuit"]
    | Literal["circuit_with_depth1_circuit_operation"]
    | Literal["circuit_with_depth2_circuit_operation"],
    request: pytest.FixtureRequest,
) -> None:
    circuit = request.getfixturevalue(circuit_fixture)
    mmap = CircuitMeasurementMap(circuit)
    qubit = cirq.GridQubit(0, 0)
    # The only measurement on qubit (0, 0) is at moment 2
    assert mmap.get_measurement_relative_offset(0, qubit, -1) is None
    assert mmap.get_measurement_relative_offset(1, qubit, -1) is None
    assert mmap.get_measurement_relative_offset(2, qubit, -1) is not None
    assert mmap.get_measurement_relative_offset(2, qubit, -2) is None


def test_measurement_map_get_measurement_relative_offset_repeat(
    circuit_with_depth1_repeated_circuit_operation: cirq.Circuit,
) -> None:
    mmap = CircuitMeasurementMap(circuit_with_depth1_repeated_circuit_operation)
    qubit = cirq.GridQubit(0, 0)
    # The only measurement on qubit (0, 0) is at moment 11
    for moment_index in range(11):
        assert mmap.get_measurement_relative_offset(moment_index, qubit, -1) is None
    assert mmap.get_measurement_relative_offset(11, qubit, -1) is not None
    assert mmap.get_measurement_relative_offset(11, qubit, -2) is None


def test_measurement_map_get_measurement_relative_offset_lot_of_measurements(
    circuit_with_repeated_measurements: cirq.Circuit,
) -> None:
    mmap = CircuitMeasurementMap(circuit_with_repeated_measurements)
    qubit = cirq.GridQubit(0, 0)
    # There are measurements from moment 0 to 9 included
    for moment_index in range(10):
        for backward_index in range(1, moment_index + 1):
            assert (
                mmap.get_measurement_relative_offset(
                    moment_index, qubit, -backward_index
                )
                is not None
            )
