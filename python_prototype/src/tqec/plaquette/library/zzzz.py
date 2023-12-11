from tqec.enums import PlaquetteQubitType
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubit
from tqec.position import Position

ZZZZPlaquette = Plaquette(
    qubits=[
        PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 0)),
        PlaquetteQubit(PlaquetteQubitType.DATA, Position(0, 2)),
        PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 0)),
        PlaquetteQubit(PlaquetteQubitType.DATA, Position(2, 2)),
        PlaquetteQubit(PlaquetteQubitType.SYNDROME, Position(1, 1)),
    ],
    layer_circuits=[],
)
