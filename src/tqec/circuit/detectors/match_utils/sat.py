from __future__ import annotations

from pysat.solvers import CryptoMinisat
from tqec.circuit.detectors.pauli import PauliString, pauli_literal_to_bools


def encode_pauli_string_cover_sat_problem_in_solver(
    solver: CryptoMinisat,
    expected_pauli_string: PauliString,
    available_pauli_strings: list[PauliString],
):
    """Build the SAT problem that should be solved to find a cover."""

    involved_qubits = frozenset(expected_pauli_string.qubits)
    for available_pauli_string in available_pauli_strings:
        involved_qubits |= frozenset(available_pauli_string.qubits)

    for qubit in involved_qubits:
        expected_X, expected_Z = pauli_literal_to_bools(expected_pauli_string[qubit])
        available_paulis_bools: list[tuple[bool, bool]] = [
            pauli_literal_to_bools(pauli[qubit]) for pauli in available_pauli_strings
        ]
        # The two following lists includes the 1-based indices of Pauli strings from
        # the provided `available_pauli_strings` input that finish with a X/Z stabilizers
        # on the current `qubit`.
        # For each index, we want to know if it should be included in the final cover or
        # not, so XORing the boolean variables representing whether or not this Pauli
        # string should be included results in the stabilizer propagated on that qubit.
        x_clause_literals = [
            pi + 1 for pi, (px, _) in enumerate(available_paulis_bools) if px
        ]
        z_clause_literals = [
            pi + 1 for pi, (_, pz) in enumerate(available_paulis_bools) if pz
        ]
        solver.add_xor_clause(x_clause_literals, value=expected_X)
        solver.add_xor_clause(z_clause_literals, value=expected_Z)
