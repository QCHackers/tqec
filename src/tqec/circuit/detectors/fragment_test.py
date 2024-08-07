import pytest
import stim
from tqec.circuit.detectors.fragment import (
    Fragment,
    FragmentLoop,
    split_stim_circuit_into_fragments,
)
from tqec.circuit.detectors.pauli import PauliString
from tqec.exceptions import TQECException


def test_creation() -> None:
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


def test_measurement_qubits() -> None:
    fragment = Fragment(stim.Circuit("M 1 2 3"))
    assert set(fragment.measurements_qubits) == {1, 2, 3}
    assert fragment.num_measurements == 3


def test_fragment_measurements_and_resets() -> None:
    fragment = Fragment(stim.Circuit("M 1 2 3"))
    assert len(fragment.resets) == 0
    assert set(fragment.measurements) == {PauliString({i: "Z"}) for i in [1, 2, 3]}

    fragment = Fragment(stim.Circuit("R 1 2 3\nTICK\nM 1 2 3"))
    assert set(fragment.measurements) == {PauliString({i: "Z"}) for i in [1, 2, 3]}
    assert set(fragment.measurements) == {PauliString({i: "Z"}) for i in [1, 2, 3]}

    fragment = Fragment(
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
    assert set(fragment.resets) == {PauliString({i: "Z"}) for i in range(5)}
    assert set(fragment.measurements) == {PauliString({i: "Z"}) for i in range(5)}


def test_get_tableau() -> None:
    measurement_only = Fragment(stim.Circuit("""M 0 1 2 """))
    reset_measurement_only = Fragment(stim.Circuit("""R 0 1 2\nTICK\nM 0 1 2"""))

    assert measurement_only.get_tableau() == stim.Tableau(3)
    assert reset_measurement_only.get_tableau() == stim.Tableau(3)

    h_gates = Fragment(stim.Circuit("""H 0 1 2\nTICK\nM 0 1 2 """))
    assert h_gates.get_tableau() == stim.Circuit("H 0 1 2").to_tableau()


def test_fragment_loop_creation() -> None:
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


def test_fragment_loop_with_repetition() -> None:
    fragment = Fragment(stim.Circuit("R 1 2 3\nTICK\nM 1 2 3"))
    fragment_loop = FragmentLoop([fragment], 10)
    assert fragment_loop.with_repetitions(1) == FragmentLoop([fragment], 1)
    assert fragment_loop.with_repetitions(10) == fragment_loop
    with pytest.raises(TQECException):
        fragment_loop.with_repetitions(0)
    with pytest.raises(TQECException):
        fragment_loop.with_repetitions(-10)


def test_split_stim_circuit_into_fragments_simple() -> None:
    fragments = split_stim_circuit_into_fragments(stim.Circuit("M 0 1 2"))
    assert len(fragments) == 1
    assert fragments[0] == Fragment(stim.Circuit("M 0 1 2"))

    fragments = split_stim_circuit_into_fragments(
        stim.Circuit("R 1 2 3\nTICK\nM 1 2 3")
    )
    assert len(fragments) == 1
    assert fragments[0] == Fragment(stim.Circuit("R 1 2 3\nTICK\nM 1 2 3"))

    one_round_qec = stim.Circuit("""
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
    fragments = split_stim_circuit_into_fragments(one_round_qec)

    assert len(fragments) == 1
    assert fragments[0] == Fragment(one_round_qec)


def test_split_stim_circuit_into_fragments_qec_repetition_code() -> None:
    circuit = stim.Circuit("""
R 0 1 2 3 4
TICK
CX 0 1 2 3
TICK
CX 2 1 4 3
TICK
M 1 3
DETECTOR(1, 0) rec[-2]
DETECTOR(3, 0) rec[-1]
TICK
REPEAT 9 {
    R 1 3
    TICK
    CX 0 1 2 3
    TICK
    CX 2 1 4 3
    TICK
    M 1 3
    SHIFT_COORDS(0, 1)
    DETECTOR(1, 0) rec[-2] rec[-4]
    DETECTOR(3, 0) rec[-1] rec[-3]
    TICK
}
M 0 2 4
DETECTOR(1, 1) rec[-2] rec[-3] rec[-5]
DETECTOR(3, 1) rec[-1] rec[-2] rec[-4]
OBSERVABLE_INCLUDE(0) rec[-1]""")
    first_round = stim.Circuit("""
R 0 1 2 3 4
TICK
CX 0 1 2 3
TICK
CX 2 1 4 3
TICK
M 1 3
DETECTOR(1, 0) rec[-2]
DETECTOR(3, 0) rec[-1]
TICK""")
    repeat_body = stim.Circuit("""
R 1 3
TICK
CX 0 1 2 3
TICK
CX 2 1 4 3
TICK
M 1 3
SHIFT_COORDS(0, 1)
DETECTOR(1, 0) rec[-2] rec[-4]
DETECTOR(3, 0) rec[-1] rec[-3]
TICK""")
    # No reset in end_round.
    # The last TICK is an implementation detail, maybe try to remove it?
    end_round = stim.Circuit("""
M 0 2 4
DETECTOR(1, 1) rec[-2] rec[-3] rec[-5]
DETECTOR(3, 1) rec[-1] rec[-2] rec[-4]
OBSERVABLE_INCLUDE(0) rec[-1]""")
    fragments = split_stim_circuit_into_fragments(circuit)
    assert len(fragments) == 3
    assert fragments[0] == Fragment(first_round)
    assert fragments[1] == FragmentLoop([Fragment(repeat_body)], 9)
    assert fragments[2] == Fragment(end_round)


def test_split_stim_circuit_into_fragments_repeat_block() -> None:
    circuit = stim.Circuit("""
REPEAT 9 {
    R 1 3
    TICK
    M 1 3
}""")
    fragments = split_stim_circuit_into_fragments(circuit)
    assert len(fragments) == 1
    assert fragments[0] == FragmentLoop(
        [Fragment(stim.Circuit("R 1 3\nTICK\nM 1 3"))], 9
    )

    erroneous_circuit = stim.Circuit("REPEAT 9 {\nR 1 3\nTICK\nH 1 3\n}")
    with pytest.raises(TQECException, match=r"^Error when splitting .* REPEAT block.*"):
        split_stim_circuit_into_fragments(erroneous_circuit)


def test_split_stim_circuit_into_fragments_error_before_repeat() -> None:
    circuit = stim.Circuit("""
R 1 3
REPEAT 9 {
    R 1 3
    TICK
    M 1 3
}""")
    with pytest.raises(
        TQECException,
        match=r"Trying to start a REPEAT block without a cleanly finished Fragment.*",
    ):
        split_stim_circuit_into_fragments(circuit)
