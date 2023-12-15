from tqec.enums import PlaquetteQubitType, PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubit
from tqec.plaquette.schedule import ScheduledCircuit
from tqec.position import Position, Shape2D

import cirq
from cirq.circuits.circuit import Circuit


class ZZPlaquette(Plaquette):
    def __init__(self, orientation: PlaquetteOrientation):
        _full_data_plaquette_qubits = [
            None,  # To have a 1-based indexing of this internal list.
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 0)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 2)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 0)),
            PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 2)),
        ]
        data_plaquette_qubit_indices: list[int]
        if orientation == PlaquetteOrientation.RIGHT:
            data_plaquette_qubit_indices = [1, 2]
        elif orientation == PlaquetteOrientation.LEFT:
            data_plaquette_qubit_indices = [3, 4]
        elif orientation == PlaquetteOrientation.DOWN:
            data_plaquette_qubit_indices = [1, 3]
        else:  # if orientation == PlaquetteOrientation.UP:
            data_plaquette_qubit_indices = [2, 4]

        data_plaquette_qubits: list[PlaquetteQubit] = [
            _full_data_plaquette_qubits[i] for i in data_plaquette_qubit_indices
        ]
        syndrome_plaquette_qubit = PlaquetteQubit(
            PlaquetteQubitType.SYNDROME, Position(1, 1)
        )
        sq = syndrome_plaquette_qubit.to_grid_qubit()
        dq = [data_qubit.to_grid_qubit() for data_qubit in data_plaquette_qubits]
        super().__init__(
            qubits=[*data_plaquette_qubits, syndrome_plaquette_qubit],
            layer_circuits=[
                ScheduledCircuit(
                    Circuit(
                        (
                            # List of moments
                            [cirq.R(sq)],
                            [cirq.H(sq)],
                            [cirq.CX(sq, dq[0])],
                            [cirq.CX(sq, dq[1])],
                            [cirq.H(sq)],
                            [cirq.M(sq, key="XX")],
                        )
                    ),
                    data_plaquette_qubit_indices,
                )
            ],
        )

    @property
    def shape(self) -> Shape2D:
        return Shape2D(3, 3)
