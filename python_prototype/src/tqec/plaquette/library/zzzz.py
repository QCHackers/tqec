from tqec.enums import PlaquetteQubitType
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubit
from tqec.position import Position

import cirq
from cirq.circuits.circuit import Circuit
from cirq import GridQubit

ZZZZPlaquette = Plaquette(
    qubits=[
        PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 0)),
        PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 2)),
        PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 0)),
        PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 2)),
        PlaquetteQubit(PlaquetteQubitType.SYNDROME, Position(1, 1)),
    ],
    layer_circuits=[
        Circuit(
            (
                # List of moments
                [cirq.R(GridQubit(1, 1))],
                # Empty moment to account for the ZZZZ stabilizer H gate and synchronise
                # CNOTs. Hardcoding this is not the right way to go, there should
                # be another way of doing that...
                [cirq.I(GridQubit(1, 1))],
                [cirq.CX(GridQubit(0, 0), GridQubit(1, 1))],
                [cirq.CX(GridQubit(0, 2), GridQubit(1, 1))],
                [cirq.CX(GridQubit(2, 0), GridQubit(1, 1))],
                [cirq.CX(GridQubit(2, 2), GridQubit(1, 1))],
                [cirq.I(GridQubit(1, 1))],
                [cirq.M(GridQubit(1, 1), key="ZZZZ")],
            )
        )
    ],
)
