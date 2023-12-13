from tqec.enums import PlaquetteQubitType
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubit
from tqec.position import Position

import cirq
from cirq.circuits.circuit import Circuit


class ZZZZPlaquette(Plaquette):
    def __init__(self):
        data_plaquette_qubits = [
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 0)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 2)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 0)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 2)),
        ]
        syndrome_plaquette_qubit = PlaquetteQubit(
            PlaquetteQubitType.SYNDROME, Position(1, 1)
        )
        sq = syndrome_plaquette_qubit.to_grid_qubit()
        dq = [data_qubit.to_grid_qubit() for data_qubit in data_plaquette_qubits]
        super().__init__(
            qubits=[*data_plaquette_qubits, syndrome_plaquette_qubit],
            layer_circuits=[
                Circuit(
                    (
                        # List of moments
                        [cirq.R(sq)],
                        # Empty moment to account for the ZZZZ stabilizer H gate and synchronise
                        # CNOTs. Hardcoding this is not the right way to go, there should
                        # be another way of doing that...
                        [cirq.I(sq)],
                        [cirq.CX(sq, dq[0])],
                        [cirq.CX(sq, dq[1])],
                        [cirq.CX(sq, dq[2])],
                        [cirq.CX(sq, dq[3])],
                        [cirq.I(sq)],
                        [cirq.M(sq, key="ZZZZ")],
                    )
                )
            ],
        )
