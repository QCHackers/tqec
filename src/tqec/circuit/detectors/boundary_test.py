import numpy
import pytest
from tqec.circuit.detectors.boundary import BoundaryStabilizer, manhattan_distance
from tqec.circuit.detectors.measurement import RelativeMeasurementLocation
from tqec.circuit.detectors.pauli import PauliString
from tqec.exceptions import TQECException


def test_boundary_stabilizer_construction():
    X0Z1 = PauliString({0: "X", 1: "Z"})
    Z0 = PauliString({0: "Z"})
    Z1 = PauliString({1: "Z"})

    BoundaryStabilizer(X0Z1, [Z0, Z1], [], frozenset([0]))
    BoundaryStabilizer(X0Z1, [], [RelativeMeasurementLocation(-1, 0)], frozenset([0]))
    BoundaryStabilizer(X0Z1, [Z0, Z0], [], frozenset([1, 4, 6]))
    with pytest.raises(TQECException):
        BoundaryStabilizer(X0Z1, [Z0, Z0], [], frozenset([]))


def test_has_anti_commuting_operations():
    X0Z1 = PauliString({0: "X", 1: "Z"})
    X0 = PauliString({0: "X"})
    Z0 = PauliString({0: "Z"})
    Z1 = PauliString({1: "Z"})

    stab = BoundaryStabilizer(X0Z1, [X0, Z1], [], frozenset([0]))
    assert not stab.has_anticommuting_operations

    stab = BoundaryStabilizer(X0Z1, [Z0, Z1], [], frozenset([0]))
    assert stab.has_anticommuting_operations

    stab = BoundaryStabilizer(X0Z1, [], [], frozenset([0]))
    assert not stab.has_anticommuting_operations


def test_boundary_stabilizer_collapsing_operations():
    X0Z1 = PauliString({0: "X", 1: "Z"})
    X0 = PauliString({0: "X"})
    Z0 = PauliString({0: "Z"})
    Z1 = PauliString({1: "Z"})

    stab = BoundaryStabilizer(X0Z1, [X0, Z1], [], frozenset([0]))
    assert set(stab.collapsing_operations) == {X0, Z1}

    stab = BoundaryStabilizer(X0Z1, [Z0, Z1], [], frozenset([0]))
    assert set(stab.collapsing_operations) == {Z0, Z1}

    stab = BoundaryStabilizer(X0Z1, [], [], frozenset([0]))
    assert not list(stab.collapsing_operations)


def test_after_and_before_collapse():
    X0Z1 = PauliString({0: "X", 1: "Z"})
    X0 = PauliString({0: "X"})
    Z0 = PauliString({0: "Z"})
    Z1 = PauliString({1: "Z"})

    stab = BoundaryStabilizer(X0Z1, [X0, Z1], [], frozenset([0]))
    assert stab.before_collapse == X0Z1
    assert stab.after_collapse == PauliString({})

    stab = BoundaryStabilizer(X0Z1, [Z0, Z1], [], frozenset([0]))
    assert stab.before_collapse == X0Z1
    with pytest.raises(TQECException):
        stab.after_collapse

    stab = BoundaryStabilizer(X0Z1, [], [], frozenset([0]))
    assert stab.before_collapse == X0Z1
    assert stab.after_collapse == X0Z1


def test_merge():
    X0Z1 = PauliString({0: "X", 1: "Z"})
    Z0X1 = PauliString({0: "Z", 1: "X"})
    Y0Y1 = PauliString({0: "Y", 1: "Y"})
    X0 = PauliString({0: "X"})
    Z0 = PauliString({0: "Z"})
    Z1 = PauliString({1: "Z"})

    a = BoundaryStabilizer(
        X0Z1,
        [X0, Z1],
        [RelativeMeasurementLocation(-28, 3), RelativeMeasurementLocation(-10, 3)],
        frozenset([1, 4, 0]),
    )
    b = BoundaryStabilizer(
        Z0X1, [X0, Z1], [RelativeMeasurementLocation(-20, 11)], frozenset([2])
    )
    c = BoundaryStabilizer(Z0X1, [Z0, Z1], [], frozenset([0]))

    ab = a.merge(b)
    assert ab.before_collapse == Y0Y1
    assert set(ab.collapsing_operations) == {X0, Z1}
    assert set(ab.involved_measurements) == set(a.involved_measurements) | set(
        b.involved_measurements
    )
    assert set(ab._source_qubits) == {0, 1, 2, 4}

    with pytest.raises(TQECException):
        a.merge(c)


def test_with_measurement_offset():
    X0Z1 = PauliString({0: "X", 1: "Z"})
    X0 = PauliString({0: "X"})
    Z1 = PauliString({1: "Z"})

    a = BoundaryStabilizer(
        X0Z1,
        [X0, Z1],
        [RelativeMeasurementLocation(-28, 3), RelativeMeasurementLocation(-10, 3)],
        frozenset([0]),
    )

    assert set(a.with_measurement_offset(9).involved_measurements) == {
        RelativeMeasurementLocation(-19, 3),
        RelativeMeasurementLocation(-1, 3),
    }
    assert set(a.with_measurement_offset(-1).involved_measurements) == {
        RelativeMeasurementLocation(-29, 3),
        RelativeMeasurementLocation(-11, 3),
    }
    with pytest.raises(
        TQECException,
        match=r"^Relative measurement offsets should be strictly negative\.$",
    ):
        a.with_measurement_offset(10)


def test_coordinates():
    X0Z1 = PauliString({0: "X", 1: "Z"})
    X0 = PauliString({0: "X"})
    Z1 = PauliString({1: "Z"})

    a = BoundaryStabilizer(
        X0Z1,
        [X0, Z1],
        [RelativeMeasurementLocation(-28, 3), RelativeMeasurementLocation(-10, 3)],
        frozenset([3]),
    )
    qubit_coordinates = (1.0, 2.0)
    numpy.testing.assert_allclose(
        a.coordinates({3: qubit_coordinates}), qubit_coordinates
    )


def test_manhattan_distance():
    X0Z1 = PauliString({0: "X", 1: "Z"})
    Z0X1 = PauliString({0: "Z", 1: "X"})
    X0 = PauliString({0: "X"})
    Z1 = PauliString({1: "Z"})

    qubits_coordinates = {i: (2.0 * i, i / 2) for i in range(10)}
    a = BoundaryStabilizer(
        X0Z1,
        [X0, Z1],
        [RelativeMeasurementLocation(-28, 3), RelativeMeasurementLocation(-10, 3)],
        frozenset([3]),
    )
    b = BoundaryStabilizer(
        Z0X1,
        [X0, Z1],
        [RelativeMeasurementLocation(-20, 6)],
        frozenset([6]),
    )
    numpy.testing.assert_allclose(a.coordinates(qubits_coordinates), (6.0, 1.5))
    numpy.testing.assert_allclose(b.coordinates(qubits_coordinates), (12.0, 3.0))
    numpy.testing.assert_allclose(manhattan_distance(a, a, qubits_coordinates), 0.0)
    numpy.testing.assert_allclose(manhattan_distance(b, b, qubits_coordinates), 0.0)
    numpy.testing.assert_allclose(manhattan_distance(a, b, qubits_coordinates), 7.5)
    numpy.testing.assert_allclose(manhattan_distance(b, a, qubits_coordinates), 7.5)
