import cirq

from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.measurement import (
    xx_measurement_plaquette,
    xxxx_measurement_plaquette,
    zz_measurement_plaquette,
    zzzz_measurement_plaquette,
)
from tqec.plaquette.library.pauli import MeasurementBasis
from tqec.plaquette.qubit import RoundedPlaquetteQubits, SquarePlaquetteQubits


def _untag(op: cirq.Operation) -> cirq.Operation:
    return op.untagged


def test_xx_measurement_plaquette():
    for measurement_basis in MeasurementBasis:
        plaquette = xx_measurement_plaquette(
            PlaquetteOrientation.UP, data_qubit_measurement_basis=measurement_basis
        )
        assert plaquette.qubits == RoundedPlaquetteQubits(PlaquetteOrientation.UP)
        (sq,) = plaquette.qubits.get_syndrome_qubits_cirq()
        dq1, dq2 = plaquette.qubits.get_data_qubits_cirq()
        assert plaquette.circuit.schedule == [1, 2, 5, 6, 7, 8]
        circuit = plaquette.circuit.raw_circuit.map_operations(lambda op: op.untagged)
        assert circuit == cirq.Circuit(
            cirq.Moment(cirq.R(sq)),
            cirq.Moment(cirq.H(sq)),
            cirq.Moment(cirq.CX(sq, dq1)),
            cirq.Moment(cirq.CX(sq, dq2)),
            cirq.Moment(cirq.H(sq)),
            cirq.Moment(cirq.M(sq), measurement_basis(dq1), measurement_basis(dq2)),
        ).map_operations(_untag)


def test_zz_measurement_plaquette():
    for measurement_basis in MeasurementBasis:
        plaquette = zz_measurement_plaquette(
            PlaquetteOrientation.UP, data_qubit_measurement_basis=measurement_basis
        )
        assert plaquette.qubits == RoundedPlaquetteQubits(PlaquetteOrientation.UP)
        (sq,) = plaquette.qubits.get_syndrome_qubits_cirq()
        dq1, dq2 = plaquette.qubits.get_data_qubits_cirq()
        assert plaquette.circuit.schedule == [1, 4, 6, 8]
        circuit = plaquette.circuit.raw_circuit.map_operations(lambda op: op.untagged)
        assert circuit == cirq.Circuit(
            cirq.Moment(cirq.R(sq)),
            cirq.Moment(cirq.CX(dq1, sq)),
            cirq.Moment(cirq.CX(dq2, sq)),
            cirq.Moment(cirq.M(sq), measurement_basis(dq1), measurement_basis(dq2)),
        ).map_operations(_untag)


def test_xxxx_measurement_plaquette():
    for measurement_basis in MeasurementBasis:
        plaquette = xxxx_measurement_plaquette(
            data_qubit_measurement_basis=measurement_basis
        )
        assert plaquette.qubits == SquarePlaquetteQubits()
        (sq,) = plaquette.qubits.get_syndrome_qubits_cirq()
        dq1, dq2, dq3, dq4 = plaquette.qubits.get_data_qubits_cirq()
        assert plaquette.circuit.schedule == [1, 2, 3, 4, 5, 6, 7, 8]
        circuit = plaquette.circuit.raw_circuit.map_operations(lambda op: op.untagged)
        assert circuit == cirq.Circuit(
            cirq.Moment(cirq.R(sq)),
            cirq.Moment(cirq.H(sq)),
            cirq.Moment(cirq.CX(sq, dq1)),
            cirq.Moment(cirq.CX(sq, dq2)),
            cirq.Moment(cirq.CX(sq, dq3)),
            cirq.Moment(cirq.CX(sq, dq4)),
            cirq.Moment(cirq.H(sq)),
            cirq.Moment(
                cirq.M(sq),
                measurement_basis(dq1),
                measurement_basis(dq2),
                measurement_basis(dq3),
                measurement_basis(dq4),
            ),
        ).map_operations(_untag)


def test_zzzz_measurement_plaquette():
    for measurement_basis in MeasurementBasis:
        plaquette = zzzz_measurement_plaquette(
            data_qubit_measurement_basis=measurement_basis
        )
        assert plaquette.qubits == SquarePlaquetteQubits().permute_data_qubits(
            [0, 2, 1, 3]
        )
        (sq,) = plaquette.qubits.get_syndrome_qubits_cirq()
        dq1, dq2, dq3, dq4 = plaquette.qubits.get_data_qubits_cirq()
        assert plaquette.circuit.schedule == [1, 3, 4, 5, 6, 8]
        circuit = plaquette.circuit.raw_circuit.map_operations(lambda op: op.untagged)
        assert circuit == cirq.Circuit(
            cirq.Moment(cirq.R(sq)),
            cirq.Moment(cirq.CX(dq1, sq)),
            cirq.Moment(cirq.CX(dq2, sq)),
            cirq.Moment(cirq.CX(dq3, sq)),
            cirq.Moment(cirq.CX(dq4, sq)),
            cirq.Moment(
                cirq.M(sq),
                measurement_basis(dq1),
                measurement_basis(dq2),
                measurement_basis(dq3),
                measurement_basis(dq4),
            ),
        ).map_operations(_untag)
