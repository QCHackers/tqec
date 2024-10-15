import stim

from tqec.plaquette.enums import (
    MeasurementBasis,
    PlaquetteOrientation,
    PlaquetteSide,
    ResetBasis,
)
from tqec.plaquette.library.zxxz import make_zxxz_surface_code_plaquette
from tqec.plaquette.qubit import PlaquetteQubits, SquarePlaquetteQubits


def test_zxxz_surface_code_memory_plaquette() -> None:
    x_plaquette = make_zxxz_surface_code_plaquette("X")
    assert x_plaquette.qubits == SquarePlaquetteQubits()
    assert "H" in x_plaquette.mergeable_instructions
    circuit = x_plaquette.circuit.get_circuit()
    assert circuit.has_flow(stim.Flow("_ZXXZ -> Z____"))
    assert circuit.has_flow(stim.Flow("1 -> _ZXXZ xor rec[-1]"))
    assert circuit == stim.Circuit("""
QUBIT_COORDS(0, 0) 0
QUBIT_COORDS(-1, -1) 1
QUBIT_COORDS(1, -1) 2
QUBIT_COORDS(-1, 1) 3
QUBIT_COORDS(1, 1) 4
R 0
TICK
H 0
TICK
CZ 0 1
TICK
H 1 2 3 4
TICK
CZ 0 3
TICK
CZ 0 2
TICK
H 1 2 3 4
TICK
CZ 0 4
TICK
H 0
TICK
M 0
""")

    z_plaquette = make_zxxz_surface_code_plaquette("Z")
    assert z_plaquette.qubits == SquarePlaquetteQubits()
    circuit = z_plaquette.circuit.get_circuit()
    assert circuit.has_flow(stim.Flow("_ZXXZ -> Z____"))
    assert circuit.has_flow(stim.Flow("1 -> _ZXXZ xor rec[-1]"))
    assert circuit == stim.Circuit("""
QUBIT_COORDS(0, 0) 0
QUBIT_COORDS(-1, -1) 1
QUBIT_COORDS(1, -1) 2
QUBIT_COORDS(-1, 1) 3
QUBIT_COORDS(1, 1) 4
R 0
TICK
H 0
TICK
CZ 0 1
TICK
H 1 2 3 4
TICK
CZ 0 2
TICK
CZ 0 3
TICK
H 1 2 3 4
TICK
CZ 0 4
TICK
H 0
TICK
M 0
""")


def test_zxxz_surface_code_init_meas_plaquette() -> None:
    x_init_meas_plaquette = make_zxxz_surface_code_plaquette(
        "X",
        ResetBasis.Z,
        MeasurementBasis.Z,
        init_meas_only_on_side=PlaquetteSide.UP,
    )
    circuit = x_init_meas_plaquette.circuit.get_circuit()
    assert circuit == stim.Circuit("""
QUBIT_COORDS(0, 0) 0
QUBIT_COORDS(-1, -1) 1
QUBIT_COORDS(1, -1) 2
QUBIT_COORDS(-1, 1) 3
QUBIT_COORDS(1, 1) 4
R 0 1 2
TICK
H 0 1
TICK
CZ 0 1
TICK
H 1 2 3 4
TICK
CZ 0 3
TICK
CZ 0 2
TICK
H 1 2 3 4
TICK
CZ 0 4
TICK
H 0 1
TICK
M 0 1 2
""")
    z_init_meas_plaquette = make_zxxz_surface_code_plaquette(
        "Z",
        ResetBasis.Z,
        MeasurementBasis.Z,
        x_boundary_orientation="HORIZONTAL",
        init_meas_only_on_side=PlaquetteSide.RIGHT,
    )
    circuit = z_init_meas_plaquette.circuit.get_circuit()
    assert circuit.has_flow(stim.Flow("1 -> _X_Z_ xor rec[-1] xor rec[-2] xor rec[-3]"))
    assert circuit == stim.Circuit("""
QUBIT_COORDS(0, 0) 0
QUBIT_COORDS(-1, -1) 1
QUBIT_COORDS(1, -1) 2
QUBIT_COORDS(-1, 1) 3
QUBIT_COORDS(1, 1) 4
R 0 2 4
TICK
H 0 1 2 3
TICK
CZ 0 1
TICK
H 1 2 3 4
TICK
CZ 0 3
TICK
CZ 0 2
TICK
H 1 2 3 4
TICK
CZ 0 4
TICK
H 0 1 2 3
TICK
M 0 2 4
""")


def test_zxxz_surface_code_projected_plaquette() -> None:
    plaquette = make_zxxz_surface_code_plaquette("X", ResetBasis.X, MeasurementBasis.X)
    qubits = plaquette.qubits
    plaquette_up = plaquette.project_on_boundary(PlaquetteOrientation.UP)
    assert plaquette_up.qubits == PlaquetteQubits(
        data_qubits=qubits.get_qubits_on_side(PlaquetteSide.DOWN),
        syndrome_qubits=qubits.syndrome_qubits,
    )
    assert plaquette_up.circuit.get_circuit() == stim.Circuit("""
QUBIT_COORDS(0, 0) 0
QUBIT_COORDS(-1, 1) 1
QUBIT_COORDS(1, 1) 2
R 0 1 2
TICK
H 0 1
TICK
TICK
H 1 2
TICK
CZ 0 1
TICK
TICK
H 1 2
TICK
CZ 0 2
TICK
H 0 1
TICK
M 0 1 2
""")
    plaquette_down = plaquette.project_on_boundary(PlaquetteOrientation.DOWN)
    assert plaquette_down.qubits == PlaquetteQubits(
        data_qubits=qubits.get_qubits_on_side(PlaquetteSide.UP),
        syndrome_qubits=qubits.syndrome_qubits,
    )
    assert plaquette_down.circuit.get_circuit() == stim.Circuit("""
QUBIT_COORDS(0, 0) 0
QUBIT_COORDS(-1, -1) 1
QUBIT_COORDS(1, -1) 2
R 0 1 2
TICK
H 0 2
TICK
CZ 0 1
TICK
H 1 2
TICK
TICK
CZ 0 2
TICK
H 1 2
TICK
TICK
H 0 2
TICK
M 0 1 2
""")
    plaquette_left = plaquette.project_on_boundary(PlaquetteOrientation.LEFT)
    assert plaquette_left.qubits == PlaquetteQubits(
        data_qubits=qubits.get_qubits_on_side(PlaquetteSide.RIGHT),
        syndrome_qubits=qubits.syndrome_qubits,
    )
    assert plaquette_left.circuit.get_circuit() == stim.Circuit("""
QUBIT_COORDS(0, 0) 0
QUBIT_COORDS(1, -1) 1
QUBIT_COORDS(1, 1) 2
R 0 1 2
TICK
H 0 1
TICK
TICK
H 1 2
TICK
TICK
CZ 0 1
TICK
H 1 2
TICK
CZ 0 2
TICK
H 0 1
TICK
M 0 1 2
""")
    plaquette_right = plaquette.project_on_boundary(PlaquetteOrientation.RIGHT)
    assert plaquette_right.qubits == PlaquetteQubits(
        data_qubits=qubits.get_qubits_on_side(PlaquetteSide.LEFT),
        syndrome_qubits=qubits.syndrome_qubits,
    )
    assert plaquette_right.circuit.get_circuit() == stim.Circuit("""
QUBIT_COORDS(0, 0) 0
QUBIT_COORDS(-1, -1) 1
QUBIT_COORDS(-1, 1) 2
R 0 1 2
TICK
H 0 2
TICK
CZ 0 1
TICK
H 1 2
TICK
CZ 0 2
TICK
TICK
H 1 2
TICK
TICK
H 0 2
TICK
M 0 1 2
""")


def test_zxxz_surface_code_horizontal_x_boundary_flow() -> None:
    plaquette = make_zxxz_surface_code_plaquette(
        "X", x_boundary_orientation="HORIZONTAL"
    )
    circuit = plaquette.circuit.get_circuit()
    assert circuit.has_flow(stim.Flow("_XZZX -> Z____"))
    assert circuit.has_flow(stim.Flow("1 -> _XZZX xor rec[-1]"))


def test_zxxz_surface_code_horizontal_x_boundary_h_cancel() -> None:
    x_plaquette = make_zxxz_surface_code_plaquette(
        "X", ResetBasis.X, x_boundary_orientation="HORIZONTAL"
    )
    assert x_plaquette.circuit.get_circuit() == stim.Circuit("""
QUBIT_COORDS(0, 0) 0
QUBIT_COORDS(-1, -1) 1
QUBIT_COORDS(1, -1) 2
QUBIT_COORDS(-1, 1) 3
QUBIT_COORDS(1, 1) 4
R 0 1 2 3 4
TICK
H 0 2 3
TICK
CZ 0 1
TICK
H 1 2 3 4
TICK
CZ 0 2
TICK
CZ 0 3
TICK
H 1 2 3 4
TICK
CZ 0 4
TICK
H 0 1 2 3 4
TICK
M 0
""")
    z_plaquette = make_zxxz_surface_code_plaquette(
        "Z",
        data_measurement=MeasurementBasis.X,
        x_boundary_orientation="HORIZONTAL",
    )
    assert z_plaquette.circuit.get_circuit() == stim.Circuit("""
QUBIT_COORDS(0, 0) 0
QUBIT_COORDS(-1, -1) 1
QUBIT_COORDS(1, -1) 2
QUBIT_COORDS(-1, 1) 3
QUBIT_COORDS(1, 1) 4
R 0
TICK
H 0 1 2 3 4
TICK
CZ 0 1
TICK
H 1 2 3 4
TICK
CZ 0 3
TICK
CZ 0 2
TICK
H 1 2 3 4
TICK
CZ 0 4
TICK
H 0 1 4
TICK
M 0 1 2 3 4
""")
