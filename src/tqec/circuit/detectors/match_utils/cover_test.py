import itertools
import typing as ty

import pytest
import stim
from tqec.circuit.detectors.match_utils.cover import (
    _all_pauli_string_combination_results,
    find_commuting_cover_on_target_qubits_sat,
    find_exact_cover_sat,
)
from tqec.circuit.detectors.pauli import PauliString, pauli_product


def _pss(pauli_string: str) -> PauliString:
    return PauliString.from_stim_pauli_string(stim.PauliString(pauli_string))


def _all_pauli_string_combination_results_alternative_implementation(
    pauli_string_list: list[PauliString],
) -> ty.Iterator[PauliString]:
    yield from (
        pauli_product([p for p, c in zip(pauli_string_list, choices) if c])
        for choices in itertools.product([True, False], repeat=len(pauli_string_list))
    )


def test_all_pauli_string_combination_results_randomized():
    paulis = [
        PauliString.from_stim_pauli_string(stim.PauliString.random(10))
        for _ in range(5)
    ]

    from_function = set(
        pauli for _, pauli in _all_pauli_string_combination_results(paulis)
    )
    from_alternative_implementation = set(
        _all_pauli_string_combination_results_alternative_implementation(paulis)
    )
    assert from_function == from_alternative_implementation


def test_all_pauli_string_combination_results():
    paulis = [PauliString({i: "Z"}) for i in range(3)]
    all_combinations = list(
        pauli for _, pauli in _all_pauli_string_combination_results(paulis)
    )
    assert len(all_combinations) == 2 ** len(paulis)
    assert set(all_combinations) == {
        PauliString({}),
        PauliString({0: "Z"}),
        PauliString({1: "Z"}),
        PauliString({2: "Z"}),
        PauliString({0: "Z", 1: "Z"}),
        PauliString({0: "Z", 2: "Z"}),
        PauliString({1: "Z", 2: "Z"}),
        PauliString({0: "Z", 1: "Z", 2: "Z"}),
    }


@pytest.mark.parametrize(
    "target,sources,expected_result",
    [
        (
            _pss("__ZZ__ZZ__"),
            [PauliString({i: "Z"}) for i in range(10)],
            [2, 3, 6, 7],
        ),
        (
            _pss("__ZZ__ZZ__"),
            [PauliString({i: "X"}) for i in range(10)],
            None,
        ),
        (
            _pss("YYYZZZ"),
            [PauliString({i: "Z"}) for i in range(6)]
            + [PauliString({i: "X"}) for i in range(6)],
            [0, 1, 2, 3, 4, 5, 6, 7, 8],
        ),
        (
            _pss("_XYZ_XYZ"),
            [PauliString({i: "Z"}) for i in range(8)]
            + [PauliString({i: "X"}) for i in range(8)],
            [2, 3, 6, 7, 9, 10, 13, 14],
        ),
        (
            _pss("_XYZ_XYZ"),
            [PauliString({i: "Z"}) for i in range(7)]  # Missing the last Z
            + [PauliString({i: "X"}) for i in range(8)],
            None,
        ),
        (
            _pss("____"),
            [PauliString({i: "Z"}) for i in range(4)]
            + [PauliString({i: "X"}) for i in range(4)],
            [],
        ),
        (
            _pss("YYYY"),
            [PauliString({i: "Z", (i + 1) % 4: "X"}) for i in range(4)],
            [0, 1, 2, 3],
        ),
        (
            _pss("X"),
            [],
            None,
        ),
        (
            _pss("_"),
            [],
            [],
        ),
    ],
)
def test_exact_match(
    target: PauliString, sources: list[PauliString], expected_result: list[int] | None
):
    obtained_result = find_exact_cover_sat(target, sources)
    # We expect the results to either both be None, or both be a list.
    assert (obtained_result is None) == (expected_result is None)
    # If they are both a list, compare them and check the post-conditon documented.
    if obtained_result is not None and expected_result is not None:
        assert set(obtained_result) == set(expected_result)
        assert pauli_product([sources[i] for i in obtained_result]) == target


@pytest.mark.parametrize(
    "target,sources,expected_result",
    [
        (
            _pss("X"),
            [],
            None,
        ),
        (
            _pss("_"),
            [],
            None,
        ),
        (
            _pss("ZZ_XX_ZZ"),
            [_pss("ZZZZZZZZ"), _pss("___YY___"), _pss("XXXXXXXX")],
            [0, 1],
        ),
        (
            _pss("ZZ_YY_ZZ"),
            [_pss("ZZZZZZZZ"), _pss("XX____XX"), _pss("XXXXXXXX")],
            [0, 1, 2],
        ),
    ],
)
def test_commuting_match(
    target: PauliString, sources: list[PauliString], expected_result: list[int] | None
):
    obtained_result = find_commuting_cover_on_target_qubits_sat(target, sources)
    # We expect the results to either both be None, or both be a list.
    assert (obtained_result is None) == (expected_result is None)
    # If they are both a list, compare them and check the post-conditon documented.
    if obtained_result is not None and expected_result is not None:
        assert set(obtained_result) == set(expected_result)
        assert pauli_product([sources[i] for i in obtained_result]).commutes(target)
