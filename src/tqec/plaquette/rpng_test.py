from tqec.plaquette.rpng import RPNG, RGN
from tqec.plaquette.rpng import RPNGDescription

from tqec.plaquette.qubit import SquarePlaquetteQubits

from stim import Circuit as stim_Circuit
import pytest

def test_validate_plaquette_from_rpng_string() -> None:
    # Invalid plaquettes
    rpng_simplified_errors = [
        '---- ---- ----', # wrong length of values
        '---- ---- --- ----', # wrong length of values
        '-z1- -z2- ---- -z4-', # wrong number of 2Q gates
        '-z1- -z4- -z3- -z4-', # wrong times for the 2Q gates
        '-z1- -z6- -z3- -z4-', # wrong times for the 2Q gates
    ]
    rpng_simplified_examples = [
        '---- ---- ---- ----',
        '-z1- -z2- -z3- -z4-',
        '-z5- -x2- -x3- -z1-',
        '-x5h -z2z -x3x hz1-',
    ]
    rpng_extended_errors = [
        'zz5 -xz1- -xz2- -xz5- -xz4-', # wrong times for the 2Q gates
        'zz5 -xz1- -xz2- -xz4- -xz4-', # wrong times for the 2Q gates
        'zz0 -xx1- ----- -xz2- ----', # wrong meas time
    ]
    rpng_extended_examples = [
        'zz6 ----- ----- ----- -----',
        'zz3 -xz1- ----- -xz2- -----',
        'zz5 -xz1- -xz2- -xz3- -xz4-',
    ]
    for rpng in rpng_simplified_errors:
        with pytest.raises(ValueError):
            RPNGDescription.from_string(corners_rpng_string = rpng)
    for rpng in rpng_simplified_examples:
        RPNGDescription.from_string(corners_rpng_string = rpng)
    for rpng in rpng_extended_errors:
        with pytest.raises(ValueError):
            RPNGDescription.from_extended_string(ancilla_and_corners_rpng_string = rpng)
    for rpng in rpng_extended_examples:
        RPNGDescription.from_extended_string(ancilla_and_corners_rpng_string = rpng)


def test_get_plaquette_from_simplified_rpng_string() -> None:
    # Usual plaquette corresponding to the ZZZZ stabilizer.
    corners_rpng_str = '-z1- -z3- -z2- -z4-'
    desc = RPNGDescription.from_string(corners_rpng_string = corners_rpng_str)
    plaquette = desc.get_plaquette()
    expected_circuit_str = '''
QUBIT_COORDS(-1, -1) 0
QUBIT_COORDS(1, -1) 1
QUBIT_COORDS(-1, 1) 2
QUBIT_COORDS(1, 1) 3
QUBIT_COORDS(0, 0) 4
RX 4
TICK
CZ 4 0
TICK
CZ 4 2
TICK
CZ 4 1
TICK
CZ 4 3
TICK
TICK
MX 4
'''
    assert stim_Circuit(expected_circuit_str) == plaquette.circuit.get_circuit()

    # Usual plaquette corresponding to the ZXXZ stabilizer with partial initialization.
    corners_rpng_str = '-z1- zx2- zx4- -z5-'
    desc = RPNGDescription.from_string(corners_rpng_string = corners_rpng_str)
    plaquette = desc.get_plaquette()
    expected_circuit_str = '''
QUBIT_COORDS(-1, -1) 0
QUBIT_COORDS(1, -1) 1
QUBIT_COORDS(-1, 1) 2
QUBIT_COORDS(1, 1) 3
QUBIT_COORDS(0, 0) 4
RZ 1 2
RX 4
TICK
CZ 4 0
TICK
CX 4 1
TICK
TICK
CX 4 2
TICK
CZ 4 3
TICK
MX 4
'''
    assert stim_Circuit(expected_circuit_str) == plaquette.circuit.get_circuit()

    # Arbitrary plaquette.
    qubits = SquarePlaquetteQubits()
    corners_rpng_str = '-x5h -z2z -x3x hz1-'
    desc = RPNGDescription.from_string(corners_rpng_string = corners_rpng_str)
    plaquette = desc.get_plaquette(qubits = qubits)
    expected_circuit_str = '''
QUBIT_COORDS(-1, -1) 0
QUBIT_COORDS(1, -1) 1
QUBIT_COORDS(-1, 1) 2
QUBIT_COORDS(1, 1) 3
QUBIT_COORDS(0, 0) 4
H 3
RX 4
TICK
CZ 4 3
TICK
CZ 4 1
TICK
CX 4 2
TICK
TICK
CX 4 0
TICK
H 0
M 1
MX 2 4
'''
    assert stim_Circuit(expected_circuit_str) == plaquette.circuit.get_circuit()


def test_get_plaquette_from_extended_rpng_string() -> None:
    # Usual plaquette corresponding to the ZZZZ stabilizer.
    ancilla_and_corners = 'zz5 -xz1- -xz2- -zz3- -zx4-'
    desc = RPNGDescription.from_extended_string(ancilla_and_corners_rpng_string=ancilla_and_corners)
    plaquette = desc.get_plaquette()
    expected_circuit_str = '''
QUBIT_COORDS(-1, -1) 0
QUBIT_COORDS(1, -1) 1
QUBIT_COORDS(-1, 1) 2
QUBIT_COORDS(1, 1) 3
QUBIT_COORDS(0, 0) 4
RZ 4
TICK
CX 0 4
TICK
CX 1 4
TICK
CZ 4 2
TICK
CX 4 3
TICK
MZ 4
'''
    assert stim_Circuit(expected_circuit_str) == plaquette.circuit.get_circuit()