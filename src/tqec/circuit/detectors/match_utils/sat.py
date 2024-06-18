from __future__ import annotations

from pysat.solvers import CryptoMinisat
from tqec.circuit.detectors.pauli import PauliString, pauli_literal_to_bools


def encode_pauli_string_exact_cover_sat_problem_in_solver(
    solver: CryptoMinisat,
    expected_pauli_string: PauliString,
    available_pauli_strings: list[PauliString],
    qubits_to_consider: frozenset[int],
):
    """Build the SAT problem that should be solved to find an exact cover.

    This function encodes the SAT problem of interest into the provided `solver`.
    As such, the provided `solver` is expected to be a newly created instance,
    and will be mutated by this function.

    The encoded problem is the following:

    Find the indices of Pauli strings in `available_pauli_strings` such that
    the product of all the corresponding Pauli strings is exactly equal to
    `expected_pauli_string` on all the qubits in `qubits_to_consider`.

    The following post-condition should be checked after solving:

    ```py
    expected_pauli_string = PauliString({})      # Fill in!
    available_pauli_strings = [PauliString({})]  # Fill in!
    qubits_to_consider = frozenset()             # Fill in!
    solver = None                                # Fill in!

    encode_pauli_string_exact_cover_sat_problem_in_solver(
        solver, expected_pauli_string, available_pauli_strings, qubits_to_consider
    )
    indices = None # Solve the problem encoded in solver and recover the indices.

    final_pauli_string = pauli_product([available_pauli_strings[i] for i in indices])
    for q in qubits_to_consider:
        assert final_pauli_string[q] == expected_pauli_string[q]
    ```

    The SAT problem contains one boolean variable per Pauli string in
    `available_pauli_strings`, deciding if the associated Pauli string should
    be part of the cover.
    The formula is quite simple: for each qubit in `qubits_to_consider`, the following
    two boolean formulas should be `True`:

    1. The X part of the resulting Pauli string, obtained from XORing the X part of each
       Pauli string weighted by the boolean variable that decides if the Pauli string should
       be included or not, should be equal to the X part of the expected final Pauli string.
    2. Same reasoning, but for the Z part.

    Note that the "should be equal to the [P] part of the expected final Pauli string" is
    natively implemented in the SAT solver used, so we do not need to adapt the formula
    with some binary logic tricks. The solver really solves a conjunction of
    `a XOR b XOR ... XOR z == [True/False]`.

    This leads to a formula with `2*len(qubits_to_consider)` XOR clauses that should all
    be verified for a cover to exist.
    Each of the `2*len(qubits_to_consider)` XOR clauses can contain up to
    `len(available_pauli_strings)` XORed items, but a simplification is made that should
    reduce that number: if the Pauli string acts trivially w.r.t the considered Pauli effect
    (X or Z), the boolean variable is removed from the formula as we know for sure that
    this particular Pauli string cannot impact the result on that specific qubit and Pauli
    effect.

    Args:
        solver: solver that will be modified in-place to encode the SAT problem.
        expected_pauli_string: target Pauli string that should be covered by strings from
            `available_pauli_strings`.
        available_pauli_strings: Pauli strings that can be used to try to cover
            `expected_pauli_string`.
        qubits_to_consider: qubits on which the cover should be exactly equal to
            `expected_pauli_string`. Qubits not listed in this input will simply be ignored
            and no restriction on the value of the resulting cover on those qubits is added.
    """

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
    """Build the SAT problem that should be solved to find a commuting cover.

    This function encodes the SAT problem of interest into the provided `solver`.
    As such, the provided `solver` is expected to be a newly created instance,
    and will be mutated by this function.

    The encoded problem is the following:

    Find the indices of Pauli strings in `available_pauli_strings` such that
    the product of all the corresponding Pauli strings commutes with
    `expected_pauli_string` on all the qubits in `qubits_to_consider`.

    The SAT problem contains one boolean variable per Pauli string in
    `available_pauli_strings`, deciding if the associated Pauli string should
    be part of the cover.
    The formula is quite simple: for each qubit in `qubits_to_consider`, the following
    two boolean formulas should be `True`:

    1. The X part of the resulting Pauli string, obtained from XORing the X part of each
       Pauli string weighted by the boolean variable that decides if the Pauli string should
       be included or not, should be equal to the X part of the expected final Pauli string
       or be equal to I.
    2. Same reasoning, but for the Z part.

    Note that the "should be equal to the [P] part of the expected final Pauli string" is
    natively implemented in the SAT solver used, so we do not need to adapt the formula
    with some binary logic tricks. The solver really solves a conjunction of
    `a XOR b XOR ... XOR z == [True/False]`.
    Also note that the "or be equal to I" part is a little bit more tricky and requires
    some care. The logic retained for each of the possible Pauli terms is explained
    inline within the code.

    The number of XOR clauses in the formula depends on the number of each Pauli terms in
    the input `expected_pauli_string` that is considered (i.e. on qubits in
    `qubits_to_consider`). Let [P] be the number of Pauli term equal to P in
    `expected_pauli_string`, the number of XOR clauses in the resulting formula is
    `(2 * [I] + [X] + [Y] + [Z]) * len(qubits_to_consider)`. That means that there
    are less clauses in the SAT problem defined in this function than in the one defined in
    :func:`encode_pauli_string_exact_cover_sat_problem_in_solver`, except if
    `expected_pauli_string` only contains identity gates, in which case the two functions
    return the same number of XOR clauses.

    Just like :func:`encode_pauli_string_exact_cover_sat_problem_in_solver`, the number
    of terms in each XOR clause can vary depending on the provided Pauli strings in
    `available_pauli_strings`.

    Also note that the problem defined above includes a trivial solution: do not include
    any Pauli string. This lead to an identity Pauli string, that will necessarilly commute
    with the provided target. A specific clause is added to the SAT problem to avoid that
    particular trivial solution.

    Args:
        solver: solver that will be modified in-place to encode the SAT problem.
        expected_pauli_string: target Pauli string that should be covered by strings from
            `available_pauli_strings`.
        available_pauli_strings: Pauli strings that can be used to try to cover
            `expected_pauli_string`.
        qubits_to_consider: qubits on which the cover should be exactly equal to
            `expected_pauli_string`. Qubits not listed in this input will simply be ignored
            and no restriction on the value of the resulting cover on those qubits is added.
    """
    # Clause to exclude the trivial solution "include no Pauli string at all"
    solver.add_clause([lit + 1 for lit in range(len(available_pauli_strings))])

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
