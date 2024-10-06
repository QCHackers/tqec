import stim

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

    q2i = plaquette.circuit.q2i
    sqi = q2i[sq]
    dqi1, dqi2 = q2i[dq1], q2i[dq2]
    assert plaquette.circuit.get_circuit(include_qubit_coords=False) == stim.Circuit(f"""
        R  {sqi}          \nTICK
        H  {sqi}          \nTICK
                            TICK
                            TICK
        CX {sqi} {dqi1}   \nTICK
        CX {sqi} {dqi2}   \nTICK
        H  {sqi}          \nTICK
        M  {sqi}""")


def test_zz_memory_plaquette() -> None:
    plaquette = zz_memory_plaquette(PlaquetteOrientation.UP)
    assert plaquette.qubits == RoundedPlaquetteQubits(PlaquetteOrientation.UP)
    (sq,) = plaquette.qubits.get_syndrome_qubits()
    dq1, dq2 = plaquette.qubits.get_data_qubits()
    assert plaquette.circuit.schedule == Schedule.from_offsets([0, 3, 5, 7])

    q2i = plaquette.circuit.q2i
    sqi = q2i[sq]
    dqi1, dqi2 = q2i[dq1], q2i[dq2]
    assert plaquette.circuit.get_circuit(include_qubit_coords=False) == stim.Circuit(f"""
        R  {sqi}          \nTICK
                            TICK
                            TICK
        CX {dqi1} {sqi}   \nTICK
                            TICK
        CX {dqi2} {sqi}   \nTICK
                            TICK
        M  {sqi}""")


def test_xxxx_memory_plaquette() -> None:
    plaquette = xxxx_memory_plaquette()
    assert plaquette.qubits == SquarePlaquetteQubits()
    (sq,) = plaquette.qubits.get_syndrome_qubits()
    dq1, dq2, dq3, dq4 = plaquette.qubits.get_data_qubits()
    assert plaquette.circuit.schedule == Schedule.from_offsets([0, 1, 2, 3, 4, 5, 6, 7])

    q2i = plaquette.circuit.q2i
    sqi = q2i[sq]
    dqi1, dqi2, dqi3, dqi4 = q2i[dq1], q2i[dq2], q2i[dq3], q2i[dq4]
    assert plaquette.circuit.get_circuit(include_qubit_coords=False) == stim.Circuit(f"""
        R  {sqi}          \nTICK
        H  {sqi}          \nTICK
        CX {sqi} {dqi1}   \nTICK
        CX {sqi} {dqi2}   \nTICK
        CX {sqi} {dqi3}   \nTICK
        CX {sqi} {dqi4}   \nTICK
        H  {sqi}          \nTICK
        M  {sqi}""")


def test_zzzz_memory_plaquette() -> None:
    plaquette = zzzz_memory_plaquette()
    assert plaquette.qubits == SquarePlaquetteQubits().permute_data_qubits([0, 2, 1, 3])
    (sq,) = plaquette.qubits.get_syndrome_qubits()
    dq1, dq2, dq3, dq4 = plaquette.qubits.get_data_qubits()
    assert plaquette.circuit.schedule == Schedule.from_offsets([0, 2, 3, 4, 5, 7])

    q2i = plaquette.circuit.q2i
    sqi = q2i[sq]
    dqi1, dqi2, dqi3, dqi4 = q2i[dq1], q2i[dq2], q2i[dq3], q2i[dq4]
    assert plaquette.circuit.get_circuit(include_qubit_coords=False) == stim.Circuit(f"""
        R  {sqi}          \nTICK
                            TICK
        CX {dqi1} {sqi}   \nTICK
        CX {dqi2} {sqi}   \nTICK
        CX {dqi3} {sqi}   \nTICK
        CX {dqi4} {sqi}   \nTICK
                            TICK
        M  {sqi}""")
