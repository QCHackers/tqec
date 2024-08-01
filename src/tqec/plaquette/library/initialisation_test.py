import cirq

from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.initialisation import (
    xx_initialisation_plaquette,
    xxxx_initialisation_plaquette,
    zz_initialisation_plaquette,
    zzzz_initialisation_plaquette,
)
from tqec.plaquette.library.pauli import ResetBasis
from tqec.plaquette.qubit import RoundedPlaquetteQubits, SquarePlaquetteQubits


def _untag(op: cirq.Operation) -> cirq.Operation:
    return op.untagged


def test_xx_initialisation_plaquette():
    for reset_basis in ResetBasis:
        plaquette = xx_initialisation_plaquette(
            PlaquetteOrientation.UP, data_qubit_reset_basis=reset_basis
        )
        assert plaquette.qubits == RoundedPlaquetteQubits(PlaquetteOrientation.UP)
        (sq,) = plaquette.qubits.get_syndrome_qubits_cirq()
        dq1, dq2 = plaquette.qubits.get_data_qubits_cirq()
        assert plaquette.circuit.schedule == [1, 2, 5, 6, 7, 8]
        circuit = plaquette.circuit.raw_circuit.map_operations(lambda op: op.untagged)
        assert circuit == cirq.Circuit(
            cirq.Moment(cirq.R(sq), reset_basis(dq1), reset_basis(dq2)),
            cirq.Moment(cirq.H(sq)),
            cirq.Moment(cirq.CX(sq, dq1)),
            cirq.Moment(cirq.CX(sq, dq2)),
            cirq.Moment(cirq.H(sq)),
            cirq.Moment(cirq.M(sq)),
        ).map_operations(_untag)


def test_zz_initialisation_plaquette():
    for reset_basis in ResetBasis:
        plaquette = zz_initialisation_plaquette(
            PlaquetteOrientation.UP, data_qubit_reset_basis=reset_basis
        )
        assert plaquette.qubits == RoundedPlaquetteQubits(PlaquetteOrientation.UP)
        (sq,) = plaquette.qubits.get_syndrome_qubits_cirq()
        dq1, dq2 = plaquette.qubits.get_data_qubits_cirq()
        assert plaquette.circuit.schedule == [1, 4, 6, 8]
        circuit = plaquette.circuit.raw_circuit.map_operations(lambda op: op.untagged)
        assert circuit == cirq.Circuit(
            cirq.Moment(cirq.R(sq), reset_basis(dq1), reset_basis(dq2)),
            cirq.Moment(cirq.CX(dq1, sq)),
            cirq.Moment(cirq.CX(dq2, sq)),
            cirq.Moment(cirq.M(sq)),
        ).map_operations(_untag)


def test_xxxx_initialisation_plaquette():
    for reset_basis in ResetBasis:
        plaquette = xxxx_initialisation_plaquette(data_qubit_reset_basis=reset_basis)
        assert plaquette.qubits == SquarePlaquetteQubits()
        (sq,) = plaquette.qubits.get_syndrome_qubits_cirq()
        dq1, dq2, dq3, dq4 = plaquette.qubits.get_data_qubits_cirq()
        assert plaquette.circuit.schedule == [1, 2, 3, 4, 5, 6, 7, 8]
        circuit = plaquette.circuit.raw_circuit.map_operations(lambda op: op.untagged)
        assert circuit == cirq.Circuit(
            cirq.Moment(
                cirq.R(sq),
                reset_basis(dq1),
                reset_basis(dq2),
                reset_basis(dq3),
                reset_basis(dq4),
            ),
            cirq.Moment(cirq.H(sq)),
            cirq.Moment(cirq.CX(sq, dq1)),
            cirq.Moment(cirq.CX(sq, dq2)),
            cirq.Moment(cirq.CX(sq, dq3)),
            cirq.Moment(cirq.CX(sq, dq4)),
            cirq.Moment(cirq.H(sq)),
            cirq.Moment(cirq.M(sq)),
        ).map_operations(_untag)


def test_zzzz_initialisation_plaquette():
    for reset_basis in ResetBasis:
        plaquette = zzzz_initialisation_plaquette(data_qubit_reset_basis=reset_basis)
        assert plaquette.qubits == SquarePlaquetteQubits().permute_data_qubits(
            [0, 2, 1, 3]
        )
        (sq,) = plaquette.qubits.get_syndrome_qubits_cirq()
        dq1, dq2, dq3, dq4 = plaquette.qubits.get_data_qubits_cirq()
        assert plaquette.circuit.schedule == [1, 3, 4, 5, 6, 8]
        circuit = plaquette.circuit.raw_circuit.map_operations(lambda op: op.untagged)
        assert circuit == cirq.Circuit(
            cirq.Moment(
                cirq.R(sq),
                reset_basis(dq1),
                reset_basis(dq2),
                reset_basis(dq3),
                reset_basis(dq4),
            ),
            cirq.Moment(cirq.CX(dq1, sq)),
            cirq.Moment(cirq.CX(dq2, sq)),
            cirq.Moment(cirq.CX(dq3, sq)),
            cirq.Moment(cirq.CX(dq4, sq)),
            cirq.Moment(cirq.M(sq)),
        ).map_operations(_untag)
