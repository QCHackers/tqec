import pytest
import stim
from tqec.circuit.detectors.pauli import (
    PauliString,
    pauli_literal_to_bools,
    pauli_product,
)
from tqec.exceptions import TQECException


def test_pauli_string_construction():
    ps1 = PauliString({0: "X", 1: "Y", 2: "Z"})
    ps2 = PauliString({0: "X", 2: "Z", 1: "Y"})
    empty = PauliString({})
    assert bool(ps1)
    assert not empty
    assert len(ps1) == 3
    assert ps1 == ps2
    assert len({ps1, ps2}) == 1
    assert ps1.overlaps(ps2)
    assert not ps1.overlaps(PauliString({3: "X"}))
    with pytest.raises(TQECException, match=r"^Invalid Pauli operator.*"):
        PauliString({0: "W"})  # type: ignore


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

    assert PauliString.from_stim_pauli_string(stim.PauliString("IXYZ")) == PauliString(
        {0: "I", 1: "X", 2: "Y", 3: "Z"}
    )

    with pytest.raises(
        TQECException, match=r"^The length specified 2 <= the maximum qubit index.*"
    ):
        pauli_string.to_stim_pauli_string(2)


def test_pauli_string_mul():
    a = PauliString({q: p for q, p in enumerate("IIIIXXXXYYYYZZZZ")})  # type:ignore
    b = PauliString({q: p for q, p in enumerate("IXYZ" * 4)})  # type:ignore
    c = PauliString({q: p for q, p in enumerate("IXYZXIZYYZIXZYXI")})  # type:ignore
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
    X0Z1 = PauliString({0: "X", 1: "Z"})
    Z0 = PauliString({0: "Z"})
    Z1 = PauliString({1: "Z"})
    X0 = PauliString({0: "X"})
    assert X0Z1.collapse_by([X0]) == Z1
    assert X0Z1.collapse_by([X0, Z1]) == PauliString({})
    with pytest.raises(TQECException):
        X0Z1.collapse_by([Z0])


def test_pauli_string_weight():
    X0Z1 = PauliString({0: "X", 1: "Z", 2: "I"})
    Z0 = PauliString({0: "Z"})
    I0to20 = PauliString({i: "I" for i in range(20)})
    assert X0Z1.weight == 2
    assert Z0.weight == 1
    assert I0to20.weight == 0


def test_pauli_string_qubit():
    X0Z1 = PauliString({0: "X", 1: "Z", 2: "I"})
    Z0 = PauliString({0: "Z"})
    I0to20 = PauliString({i: "I" for i in range(20)})
    assert Z0.qubit == 0
    with pytest.raises(TQECException):
        X0Z1.qubit
    with pytest.raises(TQECException):
        I0to20.qubit


def test_pauli_string_indexing():
    X0Z1 = PauliString({0: "X", 1: "Z", 2: "I"})
    assert X0Z1[0] == "X"
    assert X0Z1[1] == "Z"
    assert X0Z1[2] == "I"
    assert X0Z1[3] == "I"


def test_pauli_literals_to_bool():
    assert pauli_literal_to_bools("I") == (False, False)
    assert pauli_literal_to_bools("X") == (True, False)
    assert pauli_literal_to_bools("Y") == (True, True)
    assert pauli_literal_to_bools("Z") == (False, True)


def test_pauli_product():
    X0Z1 = PauliString({0: "X", 1: "Z", 2: "I"})
    Z0 = PauliString({0: "Z"})
    I0to20 = PauliString({i: "I" for i in range(20)})

    assert pauli_product([I0to20 for _ in range(20)]) == I0to20
    assert pauli_product([X0Z1 for _ in range(20)]) == I0to20
    assert pauli_product([X0Z1 for _ in range(21)]) == X0Z1
    assert pauli_product([X0Z1, Z0]) == PauliString({0: "Y", 1: "Z"})
