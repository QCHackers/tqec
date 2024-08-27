import typing
from collections import defaultdict

from tqec.block.block import (
    RepeatedPlaquettes,
    StandardComputationBlock,
    TemporalPlaquetteSequence,
)
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
from tqec.plaquette.library.pauli import MeasurementBasis, ResetBasis
from tqec.plaquette.plaquette import Plaquettes
from tqec.templates.constructions.qubit import DenseQubitSquareTemplate
from tqec.templates.scale import LinearFunction


def _zxB_block(
    dimension: LinearFunction, basis: typing.Literal["X", "Z"]
) -> StandardComputationBlock:
    reset_basis: ResetBasis = getattr(ResetBasis, basis)
    measurement_basis: MeasurementBasis = getattr(MeasurementBasis, basis)

    initial_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
            6: xx_initialisation_plaquette(
                PlaquetteOrientation.UP, data_qubit_reset_basis=reset_basis
            ),
            7: zz_initialisation_plaquette(
                PlaquetteOrientation.LEFT, data_qubit_reset_basis=reset_basis
            ),
            9: xxxx_initialisation_plaquette(data_qubit_reset_basis=reset_basis),
            10: zzzz_initialisation_plaquette(data_qubit_reset_basis=reset_basis),
            12: zz_initialisation_plaquette(
                PlaquetteOrientation.RIGHT, data_qubit_reset_basis=reset_basis
            ),
            13: xx_initialisation_plaquette(
                PlaquetteOrientation.DOWN, data_qubit_reset_basis=reset_basis
            ),
        }
    )
    repeating_plaquettes = RepeatedPlaquettes(
        Plaquettes(
            defaultdict(empty_square_plaquette)
            | {
                6: xx_memory_plaquette(PlaquetteOrientation.UP),
                7: zz_memory_plaquette(PlaquetteOrientation.LEFT),
                9: xxxx_memory_plaquette(),
                10: zzzz_memory_plaquette(),
                12: zz_memory_plaquette(PlaquetteOrientation.RIGHT),
                13: xx_memory_plaquette(PlaquetteOrientation.DOWN),
            }
        ),
        dimension - 1,
    )
    final_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
            6: xx_measurement_plaquette(
                PlaquetteOrientation.UP, data_qubit_measurement_basis=measurement_basis
            ),
            7: zz_measurement_plaquette(
                PlaquetteOrientation.LEFT,
                data_qubit_measurement_basis=measurement_basis,
            ),
            9: xxxx_measurement_plaquette(
                data_qubit_measurement_basis=measurement_basis
            ),
            10: zzzz_measurement_plaquette(
                data_qubit_measurement_basis=measurement_basis
            ),
            12: zz_measurement_plaquette(
                PlaquetteOrientation.RIGHT,
                data_qubit_measurement_basis=measurement_basis,
            ),
            13: xx_measurement_plaquette(
                PlaquetteOrientation.DOWN,
                data_qubit_measurement_basis=measurement_basis,
            ),
        }
    )
    return StandardComputationBlock(
        DenseQubitSquareTemplate(dimension),
        TemporalPlaquetteSequence(
            initial_plaquettes, repeating_plaquettes, final_plaquettes
        ),
    )


def _xzB_block(
    dimension: LinearFunction, basis: typing.Literal["X", "Z"]
) -> StandardComputationBlock:
    reset_basis: ResetBasis = getattr(ResetBasis, basis)
    measurement_basis: MeasurementBasis = getattr(MeasurementBasis, basis)

    initial_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
            6: zz_initialisation_plaquette(
                PlaquetteOrientation.UP, data_qubit_reset_basis=reset_basis
            ),
            7: xx_initialisation_plaquette(
                PlaquetteOrientation.LEFT, data_qubit_reset_basis=reset_basis
            ),
            9: zzzz_initialisation_plaquette(data_qubit_reset_basis=reset_basis),
            10: xxxx_initialisation_plaquette(data_qubit_reset_basis=reset_basis),
            12: xx_initialisation_plaquette(
                PlaquetteOrientation.RIGHT, data_qubit_reset_basis=reset_basis
            ),
            13: zz_initialisation_plaquette(
                PlaquetteOrientation.DOWN, data_qubit_reset_basis=reset_basis
            ),
        }
    )
    repeating_plaquettes = RepeatedPlaquettes(
        Plaquettes(
            defaultdict(empty_square_plaquette)
            | {
                6: zz_memory_plaquette(PlaquetteOrientation.UP),
                7: xx_memory_plaquette(PlaquetteOrientation.LEFT),
                9: zzzz_memory_plaquette(),
                10: xxxx_memory_plaquette(),
                12: xx_memory_plaquette(PlaquetteOrientation.RIGHT),
                13: zz_memory_plaquette(PlaquetteOrientation.DOWN),
            }
        ),
        dimension - 1,
    )
    final_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
            6: zz_measurement_plaquette(
                PlaquetteOrientation.UP, data_qubit_measurement_basis=measurement_basis
            ),
            7: xx_measurement_plaquette(
                PlaquetteOrientation.LEFT,
                data_qubit_measurement_basis=measurement_basis,
            ),
            9: zzzz_measurement_plaquette(
                data_qubit_measurement_basis=measurement_basis
            ),
            10: xxxx_measurement_plaquette(
                data_qubit_measurement_basis=measurement_basis
            ),
            12: xx_measurement_plaquette(
                PlaquetteOrientation.RIGHT,
                data_qubit_measurement_basis=measurement_basis,
            ),
            13: zz_measurement_plaquette(
                PlaquetteOrientation.DOWN,
                data_qubit_measurement_basis=measurement_basis,
            ),
        }
    )
    return StandardComputationBlock(
        DenseQubitSquareTemplate(dimension),
        TemporalPlaquetteSequence(
            initial_plaquettes, repeating_plaquettes, final_plaquettes
        ),
    )


def zxz_block(dimension: LinearFunction) -> StandardComputationBlock:
    return _zxB_block(dimension, "Z")


def xzz_block(dimension: LinearFunction) -> StandardComputationBlock:
    return _xzB_block(dimension, "Z")


def zxx_block(dimension: LinearFunction) -> StandardComputationBlock:
    return _zxB_block(dimension, "X")


def xzx_block(dimension: LinearFunction) -> StandardComputationBlock:
    return _xzB_block(dimension, "X")


def zzx_block(dimension: LinearFunction) -> StandardComputationBlock:
    raise TQECException("'zzx' block is not implemented yet.")


def xxz_block(dimension: LinearFunction) -> StandardComputationBlock:
    raise TQECException("'xxz' block is not implemented yet.")
