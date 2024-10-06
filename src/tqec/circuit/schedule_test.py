import random
from tkinter import Grid

import pytest
import stim

from tqec.circuit.moment import Moment
from tqec.circuit.qubit import GridQubit
from tqec.circuit.schedule import (
    Schedule,
    ScheduledCircuit,
    ScheduleException,
    remove_duplicate_instructions,
)
from tqec.exceptions import TQECException, TQECWarning

_VALID_SCHEDULED_CIRCUITS = [
    stim.Circuit(""),
    stim.Circuit("H 0 1 2"),
    stim.Circuit("H 0 1 2\nTICK\nH 0 1 2"),
    stim.Circuit("H 0 1 2\nTICK\nTICK\nTICK\nH 0 1 2"),
    stim.Circuit("QUBIT_COORDS(0.0, 0.0) 0\nQUBIT_COORDS(0.0, 1.0) 1\nH 0 1"),
    stim.Circuit("QUBIT_COORDS(0.0, 0.0) 0\nH 0\nTICK\nM 0"),
    stim.Circuit(
        "QUBIT_COORDS(0.0, 0.0) 0\nQUBIT_COORDS(0.0, 1.0) 1\nH 0\n"
        "TICK\nCX 0 1\nTICK\nM 0 1"
    ),
]


def test_schedule_construction() -> None:
    Schedule([])
    Schedule([0])
    Schedule([0, 2, 4, 6])
    Schedule(list(range(100000)))

    with pytest.raises(ScheduleException):
        Schedule([-2, 0, 1])
    with pytest.raises(ScheduleException):
        Schedule([0, 1, 1, 2])
    with pytest.raises(ScheduleException):
        Schedule([1, 0])


def test_schedule_from_offset() -> None:
    Schedule.from_offsets([])
    Schedule.from_offsets([0])
    Schedule.from_offsets([0, 2, 4, 6])
    Schedule.from_offsets(list(range(100000)))

    with pytest.raises(ScheduleException):
        Schedule.from_offsets([-2, 0, 1])
    with pytest.raises(ScheduleException):
        Schedule.from_offsets([0, 1, 1, 2])
    with pytest.raises(ScheduleException):
        Schedule.from_offsets([1, 0])


def test_schedule_len() -> None:
    assert len(Schedule([])) == 0
    assert len(Schedule([0])) == 1
    assert len(Schedule([0, 2, 4, 6])) == 4
    assert len(Schedule(list(range(100000)))) == 100000


def test_schedule_getitem() -> None:
    with pytest.raises(IndexError):
        Schedule([])[0]
    with pytest.raises(IndexError):
        Schedule([])[-1]
    assert Schedule([0])[0] == 0
    assert Schedule([0, 2, 4, 6])[2] == 4
    assert Schedule([0, 2, 4, 6])[-1] == 6
    sched = Schedule(list(range(100000)))
    for i in (random.randint(0, 99999) for _ in range(100)):
        assert sched[i] == i


def test_schedule_iter() -> None:
    assert list(Schedule([])) == []
    assert list(Schedule([0, 5, 6])) == [0, 5, 6]
    assert list(Schedule(list(range(100000)))) == list(range(100000))


def test_schedule_insert() -> None:
    schedule = Schedule([0, 3])
    with pytest.raises(ScheduleException):
        schedule.insert(0, -1)
    assert schedule.schedule == [0, 3]
    schedule.insert(1, 1)
    assert schedule.schedule == [0, 1, 3]
    schedule.insert(-1, 2)
    assert schedule.schedule == [0, 1, 2, 3]


def test_schedule_append() -> None:
    schedule = Schedule([0, 3])
    with pytest.raises(ScheduleException):
        schedule.append(-1)
    assert schedule.schedule == [0, 3]
    schedule.append(4)
    assert schedule.schedule == [0, 3, 4]
    schedule.append(5)
    assert schedule.schedule == [0, 3, 4, 5]


def test_scheduled_circuit_construction() -> None:
    ScheduledCircuit.empty()
    ScheduledCircuit.from_circuit(stim.Circuit(""))
    ScheduledCircuit.from_circuit(stim.Circuit("H 0 1 2\nTICK\nH 0 1 2"))
    ScheduledCircuit.from_circuit(stim.Circuit("H 0 1 2\nTICK\nH 0 1 2"), 1)
    ScheduledCircuit.from_circuit(stim.Circuit("H 0 1 2\nTICK\nH 0 1 2"), 498567)
    ScheduledCircuit.from_circuit(stim.Circuit("H 0 1 2\nTICK\nH 0 1 2"), [0, 1])
    ScheduledCircuit.from_circuit(
        stim.Circuit("H 0 1 2\nTICK\nH 0 1 2"), Schedule.from_offsets([0, 3])
    )

    with pytest.raises(ScheduleException):
        ScheduledCircuit.from_circuit(stim.Circuit("H 0 1 2\nTICK\nH 0 1 2"), -1)
    with pytest.raises(ScheduleException):
        ScheduledCircuit.from_circuit(stim.Circuit("H 0 1 2\nTICK\nH 0 1 2"), [1])
    with pytest.raises(ScheduleException):
        ScheduledCircuit.from_circuit(stim.Circuit("H 0 1 2\nTICK\nH 0 1 2"), [1, 2, 3])
    with pytest.raises(ScheduleException):
        ScheduledCircuit.from_circuit(stim.Circuit("REPEAT 10{\nH 0 1 2\n}"), [1])

    ScheduledCircuit([], 0, {})
    moments = [Moment(stim.Circuit("H 0 1 2")), Moment(stim.Circuit("H 0 1 2"))]
    i2q = {i: GridQubit(i, i) for i in range(3)}
    ScheduledCircuit(moments, 0, i2q)
    ScheduledCircuit(moments, [0, 1], i2q)
    ScheduledCircuit(moments, Schedule.from_offsets([0, 1]), i2q)
    with pytest.raises(ScheduleException):
        ScheduledCircuit(moments, -1, i2q)
    with pytest.raises(ScheduleException):
        ScheduledCircuit(moments, [0], i2q)
    with pytest.raises(ScheduleException):
        ScheduledCircuit(moments, [0, 1, 2], i2q)

    with pytest.raises(ScheduleException):
        ScheduledCircuit.from_circuit(
            stim.Circuit("H 0 1 2\nTICK\nQUBIT_COORDS(0, 0) 0\nH 0 1 2")
        )
    moments = [
        Moment(stim.Circuit("H 0 1 2")),
        Moment(stim.Circuit("QUBIT_COORDS(0, 0) 0\nH 0 1 2")),
    ]
    with pytest.raises(ScheduleException):
        ScheduledCircuit(moments, 0, i2q)


def test_scheduled_circuit_schedule_property() -> None:
    assert ScheduledCircuit.empty().schedule.schedule == []
    assert ScheduledCircuit.from_circuit(
        stim.Circuit("H 0 1 2\nTICK\nH 0 1 2")
    ).schedule.schedule == [0, 1]
    assert ScheduledCircuit.from_circuit(
        stim.Circuit("H 0 1 2\nTICK\nH 0 1 2"), [4, 56]
    ).schedule.schedule == [4, 56]
    moments = [Moment(stim.Circuit("H 0 1 2")), Moment(stim.Circuit("H 0 1 2"))]
    i2q = {i: GridQubit(i, i) for i in range(3)}
    assert ScheduledCircuit(moments, 0, i2q).schedule.schedule == [0, 1]


@pytest.mark.parametrize("circuit", _VALID_SCHEDULED_CIRCUITS)
def test_scheduled_circuit_get_circuit(circuit: stim.Circuit) -> None:
    assert ScheduledCircuit.from_circuit(circuit).get_circuit() == circuit


def test_scheduled_circuit_get_qubit_coords_definition_preamble() -> None:
    assert ScheduledCircuit.from_circuit(
        stim.Circuit("H 0 1")
    ).get_qubit_coords_definition_preamble() == stim.Circuit("")
    assert ScheduledCircuit.from_circuit(
        stim.Circuit("QUBIT_COORDS(0, 0) 0\nH 0 1")
    ).get_qubit_coords_definition_preamble() == stim.Circuit("QUBIT_COORDS(0, 0) 0")
    assert ScheduledCircuit.from_circuit(
        stim.Circuit("QUBIT_COORDS(0, 0) 0\nQUBIT_COORDS(-2345, 3456) 1\nH 0 1")
    ).get_qubit_coords_definition_preamble() == stim.Circuit(
        "QUBIT_COORDS(0, 0) 0\nQUBIT_COORDS(-2345, 3456) 1"
    )


@pytest.mark.parametrize("circuit", _VALID_SCHEDULED_CIRCUITS)
def test_scheduled_circuit_get_repeated_circuit(circuit: stim.Circuit) -> None:
    for repetitions in [2, 6, 1345]:
        scheduled_circuit = ScheduledCircuit.from_circuit(circuit)
        coords_preamble = scheduled_circuit.get_qubit_coords_definition_preamble()
        body_without_coords = scheduled_circuit.get_circuit(include_qubit_coords=False)
        expected_circuit = stim.Circuit(
            f"REPEAT {repetitions} {{\n{body_without_coords}\nTICK\n}}"
        )
        assert (
            ScheduledCircuit.from_circuit(circuit).get_repeated_circuit(
                repetitions, include_qubit_coords=False
            )
            == expected_circuit
        )
        assert ScheduledCircuit.from_circuit(circuit).get_repeated_circuit(
            repetitions
        ) == (coords_preamble + expected_circuit)


def test_scheduled_circuit_get_circuit_with_schedule() -> None:
    circuit = ScheduledCircuit.from_circuit(
        stim.Circuit("H 0 1 2\nTICK\nH 0 1 2"), [0, 3]
    )
    assert circuit.get_circuit() == stim.Circuit("H 0 1 2\nTICK\nTICK\nTICK\nH 0 1 2")


def test_scheduled_circuit_get_circuit_without_coords() -> None:
    circuit = ScheduledCircuit.from_circuit(
        stim.Circuit("QUBIT_COORDS(0.0, 0.0) 0\nQUBIT_COORDS(0.0, 1.0) 1\nH 0 1")
    )
    assert circuit.get_circuit(include_qubit_coords=False) == stim.Circuit("H 0 1")


def test_scheduled_circuit_qubits() -> None:
    assert ScheduledCircuit.from_circuit(stim.Circuit("")).qubits == frozenset()
    assert ScheduledCircuit.from_circuit(stim.Circuit("H 0 1 2")).qubits == frozenset()
    assert ScheduledCircuit.from_circuit(
        stim.Circuit("QUBIT_COORDS(0.0, 0.0) 0\nQUBIT_COORDS(0.0, 1.0) 1\nH 0 1")
    ).qubits == frozenset([GridQubit(0, 0), GridQubit(0, 1)])
    assert ScheduledCircuit.from_circuit(
        stim.Circuit("QUBIT_COORDS(0.0, 0.0) 0\nH 0\nTICK\nM 0")
    ).qubits == frozenset([GridQubit(0, 0)])


def test_scheduled_circuit_map_qubit_indices() -> None:
    circuit = ScheduledCircuit.from_circuit(
        stim.Circuit("QUBIT_COORDS(0.0, 0.0) 0\nQUBIT_COORDS(0.0, 1.0) 1\nH 0 1")
    )
    mapped_circuit = circuit.map_qubit_indices({0: 13, 1: 75})
    assert mapped_circuit.get_circuit() == stim.Circuit(
        "QUBIT_COORDS(0.0, 0.0) 13\nQUBIT_COORDS(0.0, 1.0) 75\nH 13 75"
    )
    assert circuit.get_circuit() == stim.Circuit(
        "QUBIT_COORDS(0.0, 0.0) 0\nQUBIT_COORDS(0.0, 1.0) 1\nH 0 1"
    )
    circuit.map_qubit_indices({0: 13, 1: 75}, inplace=True)
    assert circuit.get_circuit() == mapped_circuit.get_circuit()

    circuit = ScheduledCircuit.from_circuit(
        stim.Circuit("QUBIT_COORDS(0.0, 0.0) 0\nX 0\nTICK\nM 0\nDETECTOR(0, 0) rec[-1]")
    )
    circuit.map_qubit_indices({0: 13, 1: 75}, inplace=True)
    assert circuit.get_circuit() == stim.Circuit(
        "QUBIT_COORDS(0.0, 0.0) 13\nX 13\nTICK\nM 13\nDETECTOR(0, 0) rec[-1]"
    )


def test_scheduled_circuit_map_to_qubits() -> None:
    qubit_map = {GridQubit(0, 0): GridQubit(18, 345), GridQubit(0, 1): GridQubit(1, 0)}
    circuit = ScheduledCircuit.from_circuit(
        stim.Circuit("QUBIT_COORDS(0.0, 0.0) 0\nQUBIT_COORDS(0.0, 1.0) 1\nH 0 1")
    )
    mapped_circuit = circuit.map_to_qubits(qubit_map)
    assert mapped_circuit.get_circuit() == stim.Circuit(
        "QUBIT_COORDS(18, 345) 0\nQUBIT_COORDS(1, 0) 1\nH 0 1"
    )
    assert circuit.get_circuit() == stim.Circuit(
        "QUBIT_COORDS(0.0, 0.0) 0\nQUBIT_COORDS(0.0, 1.0) 1\nH 0 1"
    )
    circuit.map_to_qubits(qubit_map, inplace=True)
    assert circuit.get_circuit() == mapped_circuit.get_circuit()


def test_scheduled_circuit_moment_at_schedule() -> None:
    circuit = ScheduledCircuit.from_circuit(stim.Circuit("H 0 1 2\nTICK\nH 2 1 0"))
    assert circuit.moment_at_schedule(0).circuit == stim.Circuit("H 0 1 2")
    assert circuit.moment_at_schedule(1).circuit == stim.Circuit("H 2 1 0")
    assert circuit.moment_at_schedule(-1).circuit == stim.Circuit("H 2 1 0")
    assert circuit.moment_at_schedule(-2).circuit == stim.Circuit("H 0 1 2")
    with pytest.raises(TQECException):
        circuit.moment_at_schedule(2)
    with pytest.raises(TQECException):
        circuit.moment_at_schedule(-3)


def test_scheduled_circuit_modification() -> None:
    circuit = ScheduledCircuit.empty()
    circuit.append_new_moment(Moment(stim.Circuit("H 0 1 2")))
    assert circuit.get_circuit(include_qubit_coords=False) == stim.Circuit("H 0 1 2")
    circuit.add_to_schedule_index(0, Moment(stim.Circuit("H 3")))
    assert circuit.get_circuit(include_qubit_coords=False) == stim.Circuit("H 0 1 2 3")
    circuit.add_to_schedule_index(4, Moment(stim.Circuit("CX 0 1 2 3")))
    assert circuit.get_circuit(include_qubit_coords=False) == stim.Circuit(
        "H 0 1 2 3\nTICK\nTICK\nTICK\nTICK\nCX 0 1 2 3"
    )
    circuit.add_to_schedule_index(2, Moment(stim.Circuit("CX 0 1 2 3")))
    assert circuit.get_circuit(include_qubit_coords=False) == stim.Circuit(
        "H 0 1 2 3\nTICK\nTICK\nCX 0 1 2 3\nTICK\nTICK\nCX 0 1 2 3"
    )
    circuit.append_new_moment(Moment(stim.Circuit("H 2 1 0")))
    assert circuit.get_circuit(include_qubit_coords=False) == stim.Circuit(
        "H 0 1 2 3\nTICK\nTICK\nCX 0 1 2 3\nTICK\nTICK\nCX 0 1 2 3\nTICK\nH 2 1 0"
    )
    circuit.add_to_schedule_index(-1, Moment(stim.Circuit("H 3")))
    assert circuit.get_circuit(include_qubit_coords=False) == stim.Circuit(
        "H 0 1 2 3\nTICK\nTICK\nCX 0 1 2 3\nTICK\nTICK\nCX 0 1 2 3\nTICK\nH 2 1 0 3"
    )


def test_remove_duplicate_instructions() -> None:
    instructions: list[stim.CircuitInstruction] = list(
        iter(stim.Circuit("H 0 0 0 2 0 0 0 0 1 1 2 2 0 0 0 3"))
    )  # type: ignore
    expected_instructions = set(iter(stim.Circuit("H 0 1 2 3")))  # type: ignore
    assert (
        set(remove_duplicate_instructions(instructions, frozenset(["H"])))
        == expected_instructions
    )
    with pytest.warns(TQECWarning):
        # Several H gates are overlapping, which means that the returned instruction
        # list is not a valid Moment, which should raise a warning.
        assert remove_duplicate_instructions(instructions, frozenset()) == instructions

    instructions: list[stim.CircuitInstruction] = list(
        iter(stim.Circuit("H 0 1 2 3 0 1 2 3\nM 4 5 6 4 5 6 4 5 6"))
    )  # type: ignore
    with pytest.warns(TQECWarning):
        assert set(
            remove_duplicate_instructions(instructions, frozenset(["M"]))
        ) == set(iter(stim.Circuit("H 0 1 2 3 0 1 2 3\nM 4 5 6")))
    with pytest.warns(TQECWarning):
        assert set(
            remove_duplicate_instructions(instructions, frozenset(["H"]))
        ) == set(iter(stim.Circuit("H 0 1 2 3\nM 4 5 6 4 5 6 4 5 6")))
    assert set(
        remove_duplicate_instructions(instructions, frozenset(["H", "M"]))
    ) == set(iter(stim.Circuit("H 0 1 2 3\nM 4 5 6")))
