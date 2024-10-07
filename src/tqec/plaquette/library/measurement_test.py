import stim

from tqec.circuit.schedule import Schedule
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.measurement import (
    xx_measurement_plaquette,
    xxxx_measurement_plaquette,
    zz_measurement_plaquette,
    zzzz_measurement_plaquette,
)
from tqec.plaquette.library.pauli import MeasurementBasis
from tqec.plaquette.qubit import RoundedPlaquetteQubits, SquarePlaquetteQubits


def test_xx_measurement_plaquette() -> None:
    for measurement_basis in MeasurementBasis:
        plaquette = xx_measurement_plaquette(
            PlaquetteOrientation.UP, data_qubit_measurement_basis=measurement_basis
        )
        assert plaquette.qubits == RoundedPlaquetteQubits(PlaquetteOrientation.UP)
        (sq,) = plaquette.qubits.syndrome_qubits
        dq1, dq2 = plaquette.qubits.data_qubits
        assert plaquette.circuit.schedule == Schedule.from_offsets([0, 1, 4, 5, 6, 7])

        q2i = plaquette.circuit.q2i
        sqi = q2i[sq]
        dqi1, dqi2 = q2i[dq1], q2i[dq2]
        assert plaquette.circuit.get_circuit(
            include_qubit_coords=False
        ) == stim.Circuit(f"""
            R  {sqi}          \nTICK
            H  {sqi}          \nTICK
                                TICK
                                TICK
            CX {sqi} {dqi1}   \nTICK
            CX {sqi} {dqi2}   \nTICK
            H  {sqi}          \nTICK
            M  {sqi}
            {measurement_basis.instruction_name} {dqi1} {dqi2}""")


def test_zz_measurement_plaquette() -> None:
    for measurement_basis in MeasurementBasis:
        plaquette = zz_measurement_plaquette(
            PlaquetteOrientation.UP, data_qubit_measurement_basis=measurement_basis
        )
        assert plaquette.qubits == RoundedPlaquetteQubits(PlaquetteOrientation.UP)
        (sq,) = plaquette.qubits.syndrome_qubits
        dq1, dq2 = plaquette.qubits.data_qubits
        assert plaquette.circuit.schedule == Schedule.from_offsets([0, 3, 5, 7])

        q2i = plaquette.circuit.q2i
        sqi = q2i[sq]
        dqi1, dqi2 = q2i[dq1], q2i[dq2]
        assert plaquette.circuit.get_circuit(
            include_qubit_coords=False
        ) == stim.Circuit(f"""
            R  {sqi}          \nTICK
                                TICK
                                TICK
            CX {dqi1} {sqi}   \nTICK
                                TICK
            CX {dqi2} {sqi}   \nTICK
                                TICK
            M  {sqi}
            {measurement_basis.instruction_name} {dqi1} {dqi2}""")


def test_xxxx_measurement_plaquette() -> None:
    for measurement_basis in MeasurementBasis:
        plaquette = xxxx_measurement_plaquette(
            data_qubit_measurement_basis=measurement_basis
        )
        assert plaquette.qubits == SquarePlaquetteQubits()
        (sq,) = plaquette.qubits.syndrome_qubits
        dq1, dq2, dq3, dq4 = plaquette.qubits.data_qubits
        assert plaquette.circuit.schedule == Schedule.from_offsets(
            [0, 1, 2, 3, 4, 5, 6, 7]
        )

        q2i = plaquette.circuit.q2i
        sqi = q2i[sq]
        dqi1, dqi2, dqi3, dqi4 = q2i[dq1], q2i[dq2], q2i[dq3], q2i[dq4]
        assert plaquette.circuit.get_circuit(
            include_qubit_coords=False
        ) == stim.Circuit(f"""
            R  {sqi}          \nTICK
            H  {sqi}          \nTICK
            CX {sqi} {dqi1}   \nTICK
            CX {sqi} {dqi2}   \nTICK
            CX {sqi} {dqi3}   \nTICK
            CX {sqi} {dqi4}   \nTICK
            H  {sqi}          \nTICK
            M  {sqi}
            {measurement_basis.instruction_name} {dqi1} {dqi2} {dqi3} {dqi4}""")


def test_zzzz_measurement_plaquette() -> None:
    for measurement_basis in MeasurementBasis:
        plaquette = zzzz_measurement_plaquette(
            data_qubit_measurement_basis=measurement_basis
        )
        assert plaquette.qubits == SquarePlaquetteQubits().permute_data_qubits(
            [0, 2, 1, 3]
        )
        (sq,) = plaquette.qubits.syndrome_qubits
        dq1, dq2, dq3, dq4 = plaquette.qubits.data_qubits
        assert plaquette.circuit.schedule == Schedule.from_offsets([0, 2, 3, 4, 5, 7])

        q2i = plaquette.circuit.q2i
        sqi = q2i[sq]
        dqi1, dqi2, dqi3, dqi4 = q2i[dq1], q2i[dq2], q2i[dq3], q2i[dq4]
        assert plaquette.circuit.get_circuit(
            include_qubit_coords=False
        ) == stim.Circuit(f"""
            R  {sqi}          \nTICK
                                TICK
            CX {dqi1} {sqi}   \nTICK
            CX {dqi2} {sqi}   \nTICK
            CX {dqi3} {sqi}   \nTICK
            CX {dqi4} {sqi}   \nTICK
                                TICK
            M  {sqi}
            {measurement_basis.instruction_name} {dqi1} {dqi2} {dqi3} {dqi4}""")
