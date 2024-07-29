import typing

from tqec.block.block import StandardComputationBlock
from tqec.exceptions import TQECException
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


def _zx_plaquette_list(
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
    plaquette_dict = {
        6: xx_plaquette(PlaquetteOrientation.UP, [1, 2, 5, 6, 7, 8]),
        7: zz_plaquette(PlaquetteOrientation.LEFT, [1, 5, 6, 8]),
        9: xxxx_plaquette([1, 2, 3, 4, 5, 6, 7, 8]),
        10: zzzz_plaquette([1, 3, 4, 5, 6, 8]),
        12: zz_plaquette(PlaquetteOrientation.RIGHT, [1, 3, 4, 8]),
        13: xx_plaquette(PlaquetteOrientation.DOWN, [1, 2, 3, 4, 7, 8]),
    }
    return [plaquette_dict.get(i, empty_plaquette()) for i in range(1, 15)]


def _xz_plaquette_list(
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
    plaquette_dict = {
        6: zz_plaquette(PlaquetteOrientation.UP, [1, 4, 5, 8]),
        7: xx_plaquette(PlaquetteOrientation.LEFT, [1, 2, 4, 6, 7, 8]),
        9: zzzz_plaquette([1, 3, 4, 5, 6, 8]),
        10: xxxx_plaquette([1, 2, 3, 4, 5, 6, 7, 8]),
        12: xx_plaquette(PlaquetteOrientation.RIGHT, [1, 2, 4, 6, 7, 8]),
        13: zz_plaquette(PlaquetteOrientation.DOWN, [1, 3, 5, 8]),
    }
    return [plaquette_dict.get(i, empty_plaquette()) for i in range(1, 15)]


def zxz_block(dimension: LinearFunction) -> StandardComputationBlock:
    return StandardComputationBlock(
        DenseQubitSquareTemplate(dim=dimension),
        initial_plaquettes=_zx_plaquette_list(
            empty_square_plaquette,
            xx_initialisation_plaquette,
            xxxx_initialisation_plaquette,
            zz_initialisation_plaquette,
            zzzz_initialisation_plaquette,
        ),
        final_plaquettes=_zx_plaquette_list(
            empty_square_plaquette,
            xx_measurement_plaquette,
            xxxx_measurement_plaquette,
            zz_measurement_plaquette,
            zzzz_measurement_plaquette,
        ),
        repeating_plaquettes=(
            _zx_plaquette_list(
                empty_square_plaquette,
                xx_memory_plaquette,
                xxxx_memory_plaquette,
                zz_memory_plaquette,
                zzzz_memory_plaquette,
            ),
            dimension,
        ),
    )


def xzz_block(dimension: LinearFunction) -> StandardComputationBlock:
    return StandardComputationBlock(
        DenseQubitSquareTemplate(dim=dimension),
        initial_plaquettes=_xz_plaquette_list(
            empty_square_plaquette,
            xx_initialisation_plaquette,
            xxxx_initialisation_plaquette,
            zz_initialisation_plaquette,
            zzzz_initialisation_plaquette,
        ),
        final_plaquettes=_xz_plaquette_list(
            empty_square_plaquette,
            xx_measurement_plaquette,
            xxxx_measurement_plaquette,
            zz_measurement_plaquette,
            zzzz_measurement_plaquette,
        ),
        repeating_plaquettes=(
            _xz_plaquette_list(
                empty_square_plaquette,
                xx_memory_plaquette,
                xxxx_memory_plaquette,
                zz_memory_plaquette,
                zzzz_memory_plaquette,
            ),
            dimension,
        ),
    )


def zxx_block(dimension: LinearFunction) -> StandardComputationBlock:
    raise TQECException("'zxx' block is not implemented yet.")


def xzx_block(dimension: LinearFunction) -> StandardComputationBlock:
    raise TQECException("'xzx' block is not implemented yet.")


def zzx_block(dimension: LinearFunction) -> StandardComputationBlock:
    raise TQECException("'zzx' block is not implemented yet.")


def xxz_block(dimension: LinearFunction) -> StandardComputationBlock:
    raise TQECException("'xxz' block is not implemented yet.")
