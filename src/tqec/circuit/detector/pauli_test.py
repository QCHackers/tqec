import stim

from tqec.circuit.detector.pauli import PauliString


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

    assert PauliString.from_stim_pauli_string(
        stim.PauliString("IXYZ"), ignore_identity=False
    ) == PauliString({0: "I", 1: "X", 2: "Y", 3: "Z"})


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
