import stim
import pytest

from tqec.circuit.detector.detector_util import (
    PauliString,
    split_stim_circuit_into_fragments,
    Fragment,
    FragmentLoop,
)
from tqec import TQECException


def test_pauli_string_construction():
    ps1 = PauliString({0: "X", 1: "Y", 2: "Z"})
    ps2 = PauliString({0: "X", 2: "Z", 1: "Y"})
    assert len(ps1) == 3
    assert ps1 == ps2
    assert len({ps1, ps2}) == 1
    assert ps1.intersects(ps2)
    assert not ps1.intersects(PauliString({3: "X"}))


def test_pauli_string_interop_with_stim():
    stim_pauli_string = stim.PauliString.random(num_qubits=23)
    pauli_string = PauliString.from_stim_pauli_string(stim_pauli_string)
    assert (
        pauli_string.to_stim_pauli_string(length=23) * stim_pauli_string
    ).weight == 0

    pauli_string = PauliString.from_stim_pauli_string(stim.PauliString("_XYZ"))
    assert pauli_string.after(
        stim.Tableau.from_named_gate("CZ"), targets=[0, 1]
    ) == PauliString.from_stim_pauli_string(stim.PauliString("+ZXYZ"))

    assert PauliString.from_stim_pauli_string(stim.PauliString("IXYZ"), ignore_identity=False) == PauliString(
        {0: "I", 1: "X", 2: "Y", 3: "Z"}
    )


def test_pauli_string_mul():
    a = PauliString({q: p for q, p in enumerate("IIIIXXXXYYYYZZZZ")})
    b = PauliString({q: p for q, p in enumerate("IXYZ" * 4)})
    c = PauliString({q: p for q, p in enumerate("IXYZXIZYYZIXZYXI")})
    assert a * b == c


def test_pauli_string_commutation():
    a = PauliString({0: "X", 1: "Y"})
    b = PauliString({0: "Y", 1: "Z"})
    c = PauliString({0: "Z", 1: "Y"})
    assert a.commutes(b)
    assert b.commutes(a)
    assert a.anticommutes(c)
    assert c.anticommutes(a)
    assert b.commutes(c)
    assert c.commutes(b)


def test_pauli_string_collapse_by():
    a = PauliString({0: "X", 1: "Y"})
    b = PauliString({0: "Z"})
    c = PauliString({1: "X"})
    assert a.collapse_by([b]) == PauliString({0: "I", 1: "Y"})
    assert a.collapse_by([c]) == PauliString({0: "X", 1: "I"})


def test_split_stim_circuit_into_fragments():
    d = 5
    surface_code_circuit_with_mr = stim.Circuit.generated(
        code_task="surface_code:rotated_memory_x",
        distance=d,
        rounds=d,
        after_clifford_depolarization=0.001,
        after_reset_flip_probability=0.01,
        before_measure_flip_probability=0.01,
        before_round_data_depolarization=0.005,
    )
    fragments = split_stim_circuit_into_fragments(surface_code_circuit_with_mr)
    assert len(fragments) == 3
    f1, f2, f3 = fragments
    assert isinstance(f1, Fragment)
    assert isinstance(f2, FragmentLoop)
    assert isinstance(f3, Fragment)
    assert f1.circuit.num_measurements == d**2 - 1
    assert f1.circuit.num_ticks == 7
    assert len(f1.end_stabilizer_sources) == 2 * d**2 - 1
    assert len(f1.begin_stabilizer_sources) == d**2 - 1
    assert len(f1.sources_for_next_fragment) == d**2 - 1

    assert f2.repetitions == d - 1
    assert len(f2.fragments) == 1
    assert f2.fragments[0].circuit[-38:-26] == f1.circuit[-25:-13]

    assert f3.circuit.num_measurements == d**2
