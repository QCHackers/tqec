from collections import defaultdict

from tqec.block.block import RepeatedPlaquettes, StandardComputationBlock
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
from tqec.templates.constructions.qubit import DenseQubitSquareTemplate
from tqec.templates.scale import LinearFunction


def zxz_block(dimension: LinearFunction) -> StandardComputationBlock:
    return StandardComputationBlock(
        DenseQubitSquareTemplate(dim=dimension),
        initial_plaquettes=defaultdict(empty_square_plaquette)
        | {
            6: xx_initialisation_plaquette(PlaquetteOrientation.UP),
            7: zz_initialisation_plaquette(PlaquetteOrientation.LEFT),
            9: xxxx_initialisation_plaquette(),
            10: zzzz_initialisation_plaquette(),
            12: zz_initialisation_plaquette(PlaquetteOrientation.RIGHT),
            13: xx_initialisation_plaquette(PlaquetteOrientation.DOWN),
        },
        final_plaquettes=defaultdict(empty_square_plaquette)
        | {
            6: xx_measurement_plaquette(PlaquetteOrientation.UP),
            7: zz_measurement_plaquette(PlaquetteOrientation.LEFT),
            9: xxxx_measurement_plaquette(),
            10: zzzz_measurement_plaquette(),
            12: zz_measurement_plaquette(PlaquetteOrientation.RIGHT),
            13: xx_measurement_plaquette(PlaquetteOrientation.DOWN),
        },
        repeating_plaquettes=RepeatedPlaquettes(
            defaultdict(empty_square_plaquette)
            | {
                6: xx_memory_plaquette(PlaquetteOrientation.UP),
                7: zz_memory_plaquette(PlaquetteOrientation.LEFT),
                9: xxxx_memory_plaquette(),
                10: zzzz_memory_plaquette(),
                12: zz_memory_plaquette(PlaquetteOrientation.RIGHT),
                13: xx_memory_plaquette(PlaquetteOrientation.DOWN),
            },
            dimension,
        ),
    )


def xzz_block(dimension: LinearFunction) -> StandardComputationBlock:
    return StandardComputationBlock(
        DenseQubitSquareTemplate(dim=dimension),
        initial_plaquettes=defaultdict(empty_square_plaquette)
        | {
            6: zz_initialisation_plaquette(PlaquetteOrientation.UP),
            7: xx_initialisation_plaquette(PlaquetteOrientation.LEFT),
            9: zzzz_initialisation_plaquette(),
            10: xxxx_initialisation_plaquette(),
            12: xx_initialisation_plaquette(PlaquetteOrientation.RIGHT),
            13: zz_initialisation_plaquette(PlaquetteOrientation.DOWN),
        },
        final_plaquettes=defaultdict(empty_square_plaquette)
        | {
            6: zz_measurement_plaquette(PlaquetteOrientation.UP),
            7: xx_measurement_plaquette(PlaquetteOrientation.LEFT),
            9: zzzz_measurement_plaquette(),
            10: xxxx_measurement_plaquette(),
            12: xx_measurement_plaquette(PlaquetteOrientation.RIGHT),
            13: zz_measurement_plaquette(PlaquetteOrientation.DOWN),
        },
        repeating_plaquettes=RepeatedPlaquettes(
            defaultdict(empty_square_plaquette)
            | {
                6: zz_memory_plaquette(PlaquetteOrientation.UP),
                7: xx_memory_plaquette(PlaquetteOrientation.LEFT),
                9: zzzz_memory_plaquette(),
                10: xxxx_memory_plaquette(),
                12: xx_memory_plaquette(PlaquetteOrientation.RIGHT),
                13: zz_memory_plaquette(PlaquetteOrientation.DOWN),
            },
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
