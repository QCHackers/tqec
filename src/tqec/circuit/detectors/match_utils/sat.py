from __future__ import annotations

from pysat.solvers import CryptoMinisat
from tqec.circuit.detectors.pauli import PauliString, pauli_literal_to_bools


def encode_pauli_string_exact_cover_sat_problem_in_solver(
    solver: CryptoMinisat,
    expected_pauli_string: PauliString,
    available_pauli_strings: list[PauliString],
    qubits_to_consider: frozenset[int],
):
    """Build the SAT problem that should be solved to find an exact cover."""

    for qubit in qubits_to_consider:
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


def encode_pauli_string_commuting_cover_sat_problem_in_solver(
    solver: CryptoMinisat,
    expected_pauli_string: PauliString,
    available_pauli_strings: list[PauliString],
    qubits_to_consider: frozenset[int],
):
    """Build the SAT problem that should be solved to find a commuting cover."""

    for qubit in qubits_to_consider:
        expected_effect = expected_pauli_string[qubit]
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
        if expected_effect == "I":
            # Both the X and Z effect on that qubit should be OFF (i.e., identity).
            solver.add_xor_clause(x_clause_literals, value=False)
            solver.add_xor_clause(z_clause_literals, value=False)
        elif expected_effect == "X":
            # The X effect should be ON, the Z effect should be OFF.
            # Because the identity (0, 0) is also valid, X can be either ON or OFF,
            # so we do not need to restrict X effect.
            solver.add_xor_clause(z_clause_literals, value=False)
        elif expected_effect == "Y":
            # This is an expected Y effect. This means that X and Z should be both
            # ON (i.e., the Y effect) or both OFF (i.e., the identity effect).
            # Rephrasing using XOR, this is equivalent to `X_effect XOR Z_effect == 0`.
            # Note that measurements appearing twice here can be removed, as:
            # - the XOR operation is commutative (so we can re-organise the measurements
            #   to be sorted by index).
            # - b XOR b = 0.
            # - b XOR 0 = b.
            # Also, a given measurement cannot appear more than twice, so we are fine
            # just removing duplicated entries.
            solver.add_xor_clause(
                list(set(x_clause_literals) ^ set(z_clause_literals)), value=False
            )
        elif expected_effect == "Z":
            # The X effect should be OFF, the Z effect should be ON.
            # Because the identity (0, 0) is also valid, Z can be either ON or OFF,
            # so we do not need to restrict Z effect.
            solver.add_xor_clause(z_clause_literals, value=False)
