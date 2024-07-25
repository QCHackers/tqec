import typing

from tqec.block.block import StandardComputationBlock
from tqec.plaquette.enums import PlaquetteOrientation
from tqec.plaquette.library.empty import empty_square_plaquette
from tqec.plaquette.library.initialisation import (
    xx_initialisation_plaquette,
    xxxx_initialisation_plaquette,
    zz_initialisation_plaquette,
    zzzz_initialisation_plaquette,
)
from tqec.plaquette.library.measurement import (
    xx_measurement_plaquette,
    xxxx_measurement_plaquette,
    zz_measurement_plaquette,
    zzzz_measurement_plaquette,
)
from tqec.plaquette.library.memory import (
    xx_memory_plaquette,
    xxxx_memory_plaquette,
    zz_memory_plaquette,
    zzzz_memory_plaquette,
)
from tqec.plaquette.plaquette import Plaquette
from tqec.templates.constructions.qubit import DenseQubitSquareTemplate
from tqec.templates.scale import LinearFunction

_dim = LinearFunction(2, 0)


def _plaquette_list(
    empty_plaquette: typing.Callable[[], Plaquette],
    xx_plaquette: typing.Callable[[PlaquetteOrientation, list[int]], Plaquette],
    xxxx_plaquette: typing.Callable[[list[int]], Plaquette],
    zz_plaquette: typing.Callable[[PlaquetteOrientation, list[int]], Plaquette],
    zzzz_plaquette: typing.Callable[[list[int]], Plaquette],
) -> list[Plaquette]:
    # Distribution of plaquettes:
    # 1  5  6  5  6  2
    # 7  9 10  9 10 11
    # 8 10  9 10  9 12
    # 7  9 10  9 10 11
    # 8 10  9 10  9 12
    # 3 13 14 13 14  4
    return [
        # 1
        empty_plaquette(),
        empty_plaquette(),
        empty_plaquette(),
        empty_plaquette(),
        # 5
        empty_plaquette(),
        xx_plaquette(PlaquetteOrientation.UP, [1, 2, 5, 6, 7, 8]),
        zz_plaquette(PlaquetteOrientation.LEFT, [1, 5, 6, 8]),
        empty_plaquette(),
        xxxx_plaquette([1, 2, 3, 4, 5, 6, 7, 8]),
        # 10
        zzzz_plaquette([1, 3, 4, 5, 6, 8]),
        empty_plaquette(),
        zz_plaquette(PlaquetteOrientation.RIGHT, [1, 3, 4, 8]),
        xx_plaquette(PlaquetteOrientation.DOWN, [1, 2, 3, 4, 7, 8]),
        empty_plaquette(),
    ]


zxz = StandardComputationBlock(
    DenseQubitSquareTemplate(dim=_dim),
    initial_plaquettes=_plaquette_list(
        empty_square_plaquette,
        xx_initialisation_plaquette,
        xxxx_initialisation_plaquette,
        zz_initialisation_plaquette,
        zzzz_initialisation_plaquette,
    ),
    final_plaquettes=_plaquette_list(
        empty_square_plaquette,
        xx_measurement_plaquette,
        xxxx_measurement_plaquette,
        zz_measurement_plaquette,
        zzzz_measurement_plaquette,
    ),
    repeating_plaquettes=(
        _plaquette_list(
            empty_square_plaquette,
            xx_memory_plaquette,
            xxxx_memory_plaquette,
            zz_memory_plaquette,
            zzzz_memory_plaquette,
        ),
        _dim,
    ),
)
