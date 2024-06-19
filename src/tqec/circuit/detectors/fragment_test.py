import pytest
import stim
from tqec.circuit.detectors.fragment import Fragment, FragmentLoop
from tqec.exceptions import TQECException


def test_creation():
    Fragment(stim.Circuit("""M 1 2 3 4 5"""))
    Fragment(stim.Circuit("R 1 2 3\nTICK\nM 1 2 3"))
    Fragment(
        stim.Circuit("""
R 0 1 2 3 4
TICK
CX 0 1 2 3
TICK
CX 2 1 4 3
TICK
M 1 3
DETECTOR(1, 0) rec[-2]
DETECTOR(3, 0) rec[-1]
M 0 2 4
DETECTOR(1, 1) rec[-2] rec[-3] rec[-5]
DETECTOR(3, 1) rec[-1] rec[-2] rec[-4]
OBSERVABLE_INCLUDE(0) rec[-1]""")
    )
    Fragment(stim.Circuit("QUBIT_COORDS(0, 0) 0\nTICK\nM 1 2 3"))
    with pytest.raises(TQECException):
        Fragment(stim.Circuit("R 1 2 3"))
    with pytest.raises(TQECException):
        Fragment(
            stim.Circuit("""
REPEAT 10 {
    R 0 1 2 3 4
    TICK
    CX 0 1 2 3
    TICK
    CX 2 1 4 3
    TICK
    M 1 3
    DETECTOR(1, 0) rec[-2]
    DETECTOR(3, 0) rec[-1]
    M 0 2 4
    DETECTOR(1, 1) rec[-2] rec[-3] rec[-5]
    DETECTOR(3, 1) rec[-1] rec[-2] rec[-4]
    OBSERVABLE_INCLUDE(0) rec[-1]
}""")
        )
    with pytest.raises(TQECException):
        Fragment(stim.Circuit("R 1 2 3\nH 1 2 3\nTICK\nM 1 2 3"))
    with pytest.raises(TQECException):
        Fragment(stim.Circuit("M 1 2 3\nR 1 2 3"))
    with pytest.raises(TQECException):
        Fragment(stim.Circuit("H 2\nM 1 2 3"))


def test_measurement_qubits():
    fragment = Fragment(stim.Circuit("M 1 2 3"))
    assert set(fragment.measurements_qubits) == {1, 2, 3}
    assert fragment.num_measurements == 3


def test_get_tableau():
    measurement_only = Fragment(stim.Circuit("""M 0 1 2 """))
    reset_measurement_only = Fragment(stim.Circuit("""R 0 1 2\nTICK\nM 0 1 2"""))

    assert measurement_only.get_tableau() == stim.Tableau(3)
    assert reset_measurement_only.get_tableau() == stim.Tableau(3)

    h_gates = Fragment(stim.Circuit("""H 0 1 2\nTICK\nM 0 1 2 """))
    assert h_gates.get_tableau() == stim.Circuit("H 0 1 2").to_tableau()


def test_fragment_loop_creation():
    fragment = Fragment(stim.Circuit("R 1 2 3\nTICK\nM 1 2 3"))
    FragmentLoop([fragment], 10)
    FragmentLoop([fragment for _ in range(10)], 10)
    # Even though a single repetition is not really something that makes sense (why using
    # a REPEAT in that case?), it is functionally valid, so we should accept it.
    FragmentLoop([fragment], 1)
    with pytest.raises(TQECException):
        FragmentLoop([], 10)
    with pytest.raises(TQECException):
        FragmentLoop([fragment], 0)
    with pytest.raises(TQECException):
        FragmentLoop([fragment], -10)


def test_fragment_loop_with_repetition():
    fragment = Fragment(stim.Circuit("R 1 2 3\nTICK\nM 1 2 3"))
    fragment_loop = FragmentLoop([fragment], 10)
    assert fragment_loop.with_repetitions(1) == FragmentLoop([fragment], 1)
    assert fragment_loop.with_repetitions(10) == fragment_loop
    with pytest.raises(TQECException):
        fragment_loop.with_repetitions(0)
    with pytest.raises(TQECException):
        fragment_loop.with_repetitions(-10)
