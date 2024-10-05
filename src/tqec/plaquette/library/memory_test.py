from tqec.circuit.schedule import Schedule
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.memory import (
    xx_memory_plaquette,
    xxxx_memory_plaquette,
    zz_memory_plaquette,
    zzzz_memory_plaquette,
)
from tqec.plaquette.qubit import RoundedPlaquetteQubits, SquarePlaquetteQubits


def test_xx_memory_plaquette() -> None:
    plaquette = xx_memory_plaquette(PlaquetteOrientation.UP)
    assert plaquette.qubits == RoundedPlaquetteQubits(PlaquetteOrientation.UP)
    (sq,) = plaquette.qubits.get_syndrome_qubits()
    dq1, dq2 = plaquette.qubits.get_data_qubits()
    assert plaquette.circuit.schedule == Schedule.from_offsets([0, 1, 4, 5, 6, 7])
    # circuit = plaquette.circuit.circuit.map_operations(lambda op: op.untagged)
    # assert circuit == cirq.Circuit(
    #     cirq.Moment(cirq.R(sq)),
    #     cirq.Moment(cirq.H(sq)),
    #     cirq.Moment(cirq.CX(sq, dq1)),
    #     cirq.Moment(cirq.CX(sq, dq2)),
    #     cirq.Moment(cirq.H(sq)),
    #     cirq.Moment(cirq.M(sq)),
    # )


def test_zz_memory_plaquette() -> None:
    plaquette = zz_memory_plaquette(PlaquetteOrientation.UP)
    assert plaquette.qubits == RoundedPlaquetteQubits(PlaquetteOrientation.UP)
    (sq,) = plaquette.qubits.get_syndrome_qubits()
    dq1, dq2 = plaquette.qubits.get_data_qubits()
    assert plaquette.circuit.schedule == Schedule.from_offsets([0, 3, 5, 7])
    # circuit = plaquette.circuit.circuit.map_operations(lambda op: op.untagged)
    # assert circuit == cirq.Circuit(
    #     cirq.Moment(cirq.R(sq)),
    #     cirq.Moment(cirq.CX(dq1, sq)),
    #     cirq.Moment(cirq.CX(dq2, sq)),
    #     cirq.Moment(cirq.M(sq)),
    # )


def test_xxxx_memory_plaquette() -> None:
    plaquette = xxxx_memory_plaquette()
    assert plaquette.qubits == SquarePlaquetteQubits()
    (sq,) = plaquette.qubits.get_syndrome_qubits()
    dq1, dq2, dq3, dq4 = plaquette.qubits.get_data_qubits()
    assert plaquette.circuit.schedule == Schedule.from_offsets([0, 1, 2, 3, 4, 5, 6, 7])
    # circuit = plaquette.circuit.circuit.map_operations(lambda op: op.untagged)
    # assert circuit == cirq.Circuit(
    #     cirq.Moment(cirq.R(sq)),
    #     cirq.Moment(cirq.H(sq)),
    #     cirq.Moment(cirq.CX(sq, dq1)),
    #     cirq.Moment(cirq.CX(sq, dq2)),
    #     cirq.Moment(cirq.CX(sq, dq3)),
    #     cirq.Moment(cirq.CX(sq, dq4)),
    #     cirq.Moment(cirq.H(sq)),
    #     cirq.Moment(cirq.M(sq)),
    # )


def test_zzzz_memory_plaquette() -> None:
    plaquette = zzzz_memory_plaquette()
    assert plaquette.qubits == SquarePlaquetteQubits().permute_data_qubits([0, 2, 1, 3])
    (sq,) = plaquette.qubits.get_syndrome_qubits()
    dq1, dq2, dq3, dq4 = plaquette.qubits.get_data_qubits()
    assert plaquette.circuit.schedule == Schedule.from_offsets([0, 2, 3, 4, 5, 7])
    # circuit = plaquette.circuit.circuit.map_operations(lambda op: op.untagged)
    # assert circuit == cirq.Circuit(
    #     cirq.Moment(cirq.R(sq)),
    #     cirq.Moment(cirq.CX(dq1, sq)),
    #     cirq.Moment(cirq.CX(dq2, sq)),
    #     cirq.Moment(cirq.CX(dq3, sq)),
    #     cirq.Moment(cirq.CX(dq4, sq)),
    #     cirq.Moment(cirq.M(sq)),
    # )
