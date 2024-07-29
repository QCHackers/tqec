from collections import defaultdict

import cirq
from tqec.block.block import StandardComputationBlock
from tqec.block.library.closed import xzz_block, zxz_block
from tqec.exceptions import TQECException
from tqec.plaquette.enums import PlaquetteOrientation, PlaquetteSide
from tqec.plaquette.library.empty import empty_square_plaquette
from tqec.plaquette.library.initialisation import (
    xx_initialisation_plaquette,
    xxxx_initialisation_plaquette,
    zzzz_initialisation_plaquette,
)
from tqec.plaquette.library.measurement import (
    xx_measurement_plaquette,
    xxxx_measurement_plaquette,
    zzzz_measurement_plaquette,
)
from tqec.plaquette.library.memory import (
    xx_memory_plaquette,
    xxxx_memory_plaquette,
    zzzz_memory_plaquette,
)
from tqec.plaquette.library.pauli import MeasurementBasis, ResetBasis
from tqec.plaquette.plaquette import Plaquette
from tqec.templates.constructions.qubit import (
    QubitHorizontalBorders,
    QubitVerticalBorders,
)
from tqec.templates.scale import LinearFunction


def _with_resets_on_data_qubits_on_side(
    plaquette: Plaquette,
    side: PlaquetteSide,
    reset_basis: ResetBasis = ResetBasis.Z,
    reset_moment_index: int = 1,
) -> Plaquette:
    qubits = plaquette.qubits.get_qubits_on_side(side)

    plaquette.circuit.add_to_schedule_index(
        reset_moment_index, cirq.Moment(reset_basis(q.to_grid_qubit()) for q in qubits)
    )
    return plaquette


def _with_measurements_on_data_qubits_on_side(
    plaquette: Plaquette,
    side: PlaquetteSide,
    measurement_basis: MeasurementBasis = MeasurementBasis.Z,
    measurement_moment_index: int = 8,
) -> Plaquette:
    qubits = plaquette.qubits.get_qubits_on_side(side)

    plaquette.circuit.add_to_schedule_index(
        measurement_moment_index,
        cirq.Moment(measurement_basis(q.to_grid_qubit()) for q in qubits),
    )
    return plaquette


def ozx_block(dimension: LinearFunction) -> StandardComputationBlock:
    raise TQECException("'ozx' block is not implemented yet.")


def oxz_block(dimension: LinearFunction) -> StandardComputationBlock:
    return StandardComputationBlock(
        QubitVerticalBorders(dimension),
        initial_plaquettes=defaultdict(empty_square_plaquette)
        | {
            2: _with_resets_on_data_qubits_on_side(
                xxxx_initialisation_plaquette(), PlaquetteSide.RIGHT
            ),
            3: zzzz_initialisation_plaquette(),
            4: _with_resets_on_data_qubits_on_side(
                xx_initialisation_plaquette(PlaquetteOrientation.DOWN),
                PlaquetteSide.RIGHT,
            ),
            5: xx_initialisation_plaquette(PlaquetteOrientation.UP),
            6: zzzz_initialisation_plaquette(),
            7: xxxx_initialisation_plaquette(),
        },
        final_plaquettes=defaultdict(empty_square_plaquette)
        | {
            2: _with_measurements_on_data_qubits_on_side(
                xxxx_measurement_plaquette(), PlaquetteSide.RIGHT
            ),
            3: zzzz_measurement_plaquette(),
            4: _with_measurements_on_data_qubits_on_side(
                xx_measurement_plaquette(PlaquetteOrientation.DOWN), PlaquetteSide.RIGHT
            ),
            5: xx_measurement_plaquette(PlaquetteOrientation.UP),
            6: zzzz_measurement_plaquette(),
            7: xxxx_measurement_plaquette(),
        },
        repeating_plaquettes=(
            defaultdict(empty_square_plaquette)
            | {
                2: xxxx_memory_plaquette(),
                3: zzzz_memory_plaquette(),
                4: xx_memory_plaquette(PlaquetteOrientation.DOWN),
                5: xx_memory_plaquette(PlaquetteOrientation.UP),
                6: zzzz_memory_plaquette(),
                7: xxxx_memory_plaquette(),
            },
            dimension,
        ),
    )


def xoz_block(dimension: LinearFunction) -> StandardComputationBlock:
    return StandardComputationBlock(
        QubitHorizontalBorders(dimension),
        initial_plaquettes=defaultdict(empty_square_plaquette)
        | {
            1: _with_resets_on_data_qubits_on_side(
                xx_initialisation_plaquette(PlaquetteOrientation.LEFT),
                PlaquetteSide.DOWN,
            ),
            2: zzzz_initialisation_plaquette(),
            3: _with_resets_on_data_qubits_on_side(
                xxxx_initialisation_plaquette(),
                PlaquetteSide.DOWN,
            ),
            6: xxxx_initialisation_plaquette(),
            7: zzzz_initialisation_plaquette(),
            8: xx_initialisation_plaquette(PlaquetteOrientation.RIGHT),
        },
        final_plaquettes=defaultdict(empty_square_plaquette)
        | {
            1: _with_measurements_on_data_qubits_on_side(
                xx_measurement_plaquette(PlaquetteOrientation.LEFT),
                PlaquetteSide.DOWN,
            ),
            2: zzzz_measurement_plaquette(),
            3: _with_measurements_on_data_qubits_on_side(
                xxxx_measurement_plaquette(),
                PlaquetteSide.DOWN,
            ),
            6: xxxx_measurement_plaquette(),
            7: zzzz_measurement_plaquette(),
            8: xx_measurement_plaquette(PlaquetteOrientation.RIGHT),
        },
        repeating_plaquettes=(
            defaultdict(empty_square_plaquette)
            | {
                1: xx_memory_plaquette(PlaquetteOrientation.LEFT),
                2: zzzz_memory_plaquette(),
                3: xxxx_memory_plaquette(),
                6: xxxx_memory_plaquette(),
                7: zzzz_memory_plaquette(),
                8: xx_memory_plaquette(PlaquetteOrientation.RIGHT),
            },
            dimension,
        ),
    )


def zox_block(dimension: LinearFunction) -> StandardComputationBlock:
    raise TQECException("'zox' block is not implemented yet.")


def xzo_block(dimension: LinearFunction) -> StandardComputationBlock:
    xzz = xzz_block(dimension)
    xzz.repeating_plaquettes = None
    return xzz


def zxo_block(dimension: LinearFunction) -> StandardComputationBlock:
    zxz = zxz_block(dimension)
    zxz.repeating_plaquettes = None
    return zxz
