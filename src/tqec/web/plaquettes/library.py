from tqec.circuit.schemas import SupportedCircuitTypeEnum
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.library.empty import empty_plaquette
from tqec.plaquette.library.initialisation import (
    x_initialisation_plaquette,
    z_initialisation_plaquette,
)
from tqec.plaquette.library.measurement import measurement_plaquette
from tqec.plaquette.library.xx import xx_memory_plaquette
from tqec.plaquette.library.xxxx import xxxx_memory_plaquette
from tqec.plaquette.library.zz import zz_memory_plaquette
from tqec.plaquette.library.zzzz import zzzz_memory_plaquette
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import RoundedPlaquetteQubits, SquarePlaquetteQubits
from tqec.plaquette.schemas import PlaquetteLibraryModel


class PlaquetteLibrary:
    def __init__(self) -> None:
        self._plaquettes: list[Plaquette] = []

    def add_plaquette(self, plaquette: Plaquette):
        self._plaquettes.append(plaquette)

    def remove_plaquette(self, index: int):
        self._plaquettes.pop(index)

    def to_model(self, encoding: SupportedCircuitTypeEnum) -> PlaquetteLibraryModel:
        return PlaquetteLibraryModel(
            plaquettes=[p.to_model(encoding) for p in self._plaquettes]
        )


_PLAQUETTE_QUBITS = [SquarePlaquetteQubits()] + [
    RoundedPlaquetteQubits(orientation) for orientation in PlaquetteOrientation
]
PREDEFINED_PLAQUETTES_LIBRARY = PlaquetteLibrary()
for _pq in _PLAQUETTE_QUBITS:
    PREDEFINED_PLAQUETTES_LIBRARY.add_plaquette(empty_plaquette(_pq))
    PREDEFINED_PLAQUETTES_LIBRARY.add_plaquette(measurement_plaquette(_pq, False))
    PREDEFINED_PLAQUETTES_LIBRARY.add_plaquette(x_initialisation_plaquette(_pq))
    PREDEFINED_PLAQUETTES_LIBRARY.add_plaquette(z_initialisation_plaquette(_pq))
PREDEFINED_PLAQUETTES_LIBRARY.add_plaquette(
    xxxx_memory_plaquette([1, 2, 3, 4, 5, 6, 7, 8], False)
)
PREDEFINED_PLAQUETTES_LIBRARY.add_plaquette(
    zzzz_memory_plaquette([1, 3, 4, 5, 6, 8], False)
)
for orientation in PlaquetteOrientation:
    PREDEFINED_PLAQUETTES_LIBRARY.add_plaquette(
        xx_memory_plaquette(orientation, [1, 2, 5, 6, 7, 8], False)
    )
    PREDEFINED_PLAQUETTES_LIBRARY.add_plaquette(
        zz_memory_plaquette(orientation, [1, 3, 4, 8], False)
    )
