from collections import defaultdict

import cirq
from tqec.block.block import (
    RepeatedPlaquettes,
    StandardComputationBlock,
    TemporalPlaquetteSequence,
)
from tqec.block.library.closed import xzz_block, zxz_block
from tqec.plaquette.enums import PlaquetteOrientation, PlaquetteSide
from tqec.plaquette.library.empty import empty_square_plaquette
from tqec.plaquette.library.memory import (
    xx_memory_plaquette,
    xxxx_memory_plaquette,
    zz_memory_plaquette,
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
    initial_plaquettes = defaultdict(empty_square_plaquette) | {
        2: _with_resets_on_data_qubits_on_side(
            zzzz_memory_plaquette(), PlaquetteSide.RIGHT, reset_basis=ResetBasis.X
        ),
        3: xxxx_memory_plaquette(),
        4: _with_resets_on_data_qubits_on_side(
            zz_memory_plaquette(PlaquetteOrientation.DOWN),
            PlaquetteSide.RIGHT,
            reset_basis=ResetBasis.X,
        ),
        5: zz_memory_plaquette(PlaquetteOrientation.UP),
        6: xxxx_memory_plaquette(),
        7: zzzz_memory_plaquette(),
    }
    repeating_plaquettes = RepeatedPlaquettes(
        defaultdict(empty_square_plaquette)
        | {
            2: zzzz_memory_plaquette(),
            3: xxxx_memory_plaquette(),
            4: zz_memory_plaquette(PlaquetteOrientation.DOWN),
            5: zz_memory_plaquette(PlaquetteOrientation.UP),
            6: xxxx_memory_plaquette(),
            7: zzzz_memory_plaquette(),
        },
        dimension - 1,
    )
    final_plaquettes = defaultdict(empty_square_plaquette) | {
        2: _with_measurements_on_data_qubits_on_side(
            zzzz_memory_plaquette(),
            PlaquetteSide.RIGHT,
            measurement_basis=MeasurementBasis.X,
        ),
        3: xxxx_memory_plaquette(),
        4: _with_measurements_on_data_qubits_on_side(
            zz_memory_plaquette(PlaquetteOrientation.DOWN),
            PlaquetteSide.RIGHT,
            measurement_basis=MeasurementBasis.X,
        ),
        5: zz_memory_plaquette(PlaquetteOrientation.UP),
        6: xxxx_memory_plaquette(),
        7: zzzz_memory_plaquette(),
    }
    return StandardComputationBlock(
        QubitVerticalBorders(dimension),
        TemporalPlaquetteSequence(
            initial_plaquettes, repeating_plaquettes, final_plaquettes
        ),
    )


def oxz_block(dimension: LinearFunction) -> StandardComputationBlock:
    initial_plaquettes = defaultdict(empty_square_plaquette) | {
        2: _with_resets_on_data_qubits_on_side(
            xxxx_memory_plaquette(), PlaquetteSide.RIGHT
        ),
        3: zzzz_memory_plaquette(),
        4: _with_resets_on_data_qubits_on_side(
            xx_memory_plaquette(PlaquetteOrientation.DOWN),
            PlaquetteSide.RIGHT,
        ),
        5: xx_memory_plaquette(PlaquetteOrientation.UP),
        6: zzzz_memory_plaquette(),
        7: xxxx_memory_plaquette(),
    }
    repeating_plaquettes = RepeatedPlaquettes(
        defaultdict(empty_square_plaquette)
        | {
            2: xxxx_memory_plaquette(),
            3: zzzz_memory_plaquette(),
            4: xx_memory_plaquette(PlaquetteOrientation.DOWN),
            5: xx_memory_plaquette(PlaquetteOrientation.UP),
            6: zzzz_memory_plaquette(),
            7: xxxx_memory_plaquette(),
        },
        dimension - 1,
    )
    final_plaquettes = defaultdict(empty_square_plaquette) | {
        2: _with_measurements_on_data_qubits_on_side(
            xxxx_memory_plaquette(), PlaquetteSide.RIGHT
        ),
        3: zzzz_memory_plaquette(),
        4: _with_measurements_on_data_qubits_on_side(
            xx_memory_plaquette(PlaquetteOrientation.DOWN), PlaquetteSide.RIGHT
        ),
        5: xx_memory_plaquette(PlaquetteOrientation.UP),
        6: zzzz_memory_plaquette(),
        7: xxxx_memory_plaquette(),
    }
    return StandardComputationBlock(
        QubitVerticalBorders(dimension),
        TemporalPlaquetteSequence(
            initial_plaquettes, repeating_plaquettes, final_plaquettes
        ),
    )


def xoz_block(dimension: LinearFunction) -> StandardComputationBlock:
    initial_plaquettes = defaultdict(empty_square_plaquette) | {
        1: _with_resets_on_data_qubits_on_side(
            xx_memory_plaquette(PlaquetteOrientation.LEFT),
            PlaquetteSide.DOWN,
        ),
        2: zzzz_memory_plaquette(),
        3: _with_resets_on_data_qubits_on_side(
            xxxx_memory_plaquette(),
            PlaquetteSide.DOWN,
        ),
        6: xxxx_memory_plaquette(),
        7: zzzz_memory_plaquette(),
        8: xx_memory_plaquette(PlaquetteOrientation.RIGHT),
    }
    repeating_plaquettes = RepeatedPlaquettes(
        defaultdict(empty_square_plaquette)
        | {
            1: xx_memory_plaquette(PlaquetteOrientation.LEFT),
            2: zzzz_memory_plaquette(),
            3: xxxx_memory_plaquette(),
            6: xxxx_memory_plaquette(),
            7: zzzz_memory_plaquette(),
            8: xx_memory_plaquette(PlaquetteOrientation.RIGHT),
        },
        dimension - 1,
    )
    final_plaquettes = defaultdict(empty_square_plaquette) | {
        1: _with_measurements_on_data_qubits_on_side(
            xx_memory_plaquette(PlaquetteOrientation.LEFT),
            PlaquetteSide.DOWN,
        ),
        2: zzzz_memory_plaquette(),
        3: _with_measurements_on_data_qubits_on_side(
            xxxx_memory_plaquette(),
            PlaquetteSide.DOWN,
        ),
        6: xxxx_memory_plaquette(),
        7: zzzz_memory_plaquette(),
        8: xx_memory_plaquette(PlaquetteOrientation.RIGHT),
    }
    return StandardComputationBlock(
        QubitHorizontalBorders(dimension),
        TemporalPlaquetteSequence(
            initial_plaquettes, repeating_plaquettes, final_plaquettes
        ),
    )


def zox_block(dimension: LinearFunction) -> StandardComputationBlock:
    initial_plaquettes = defaultdict(empty_square_plaquette) | {
        1: _with_resets_on_data_qubits_on_side(
            zz_memory_plaquette(PlaquetteOrientation.LEFT),
            PlaquetteSide.DOWN,
            reset_basis=ResetBasis.X,
        ),
        2: xxxx_memory_plaquette(),
        3: _with_resets_on_data_qubits_on_side(
            zzzz_memory_plaquette(), PlaquetteSide.DOWN, reset_basis=ResetBasis.X
        ),
        6: zzzz_memory_plaquette(),
        7: xxxx_memory_plaquette(),
        8: zz_memory_plaquette(PlaquetteOrientation.RIGHT),
    }
    repeating_plaquettes = RepeatedPlaquettes(
        defaultdict(empty_square_plaquette)
        | {
            1: zz_memory_plaquette(PlaquetteOrientation.LEFT),
            2: xxxx_memory_plaquette(),
            3: zzzz_memory_plaquette(),
            6: zzzz_memory_plaquette(),
            7: xxxx_memory_plaquette(),
            8: zz_memory_plaquette(PlaquetteOrientation.RIGHT),
        },
        dimension - 1,
    )
    final_plaquettes = defaultdict(empty_square_plaquette) | {
        1: _with_measurements_on_data_qubits_on_side(
            zz_memory_plaquette(PlaquetteOrientation.LEFT),
            PlaquetteSide.DOWN,
            measurement_basis=MeasurementBasis.X,
        ),
        2: xxxx_memory_plaquette(),
        3: _with_measurements_on_data_qubits_on_side(
            zzzz_memory_plaquette(),
            PlaquetteSide.DOWN,
            measurement_basis=MeasurementBasis.X,
        ),
        6: zzzz_memory_plaquette(),
        7: xxxx_memory_plaquette(),
        8: zz_memory_plaquette(PlaquetteOrientation.RIGHT),
    }
    return StandardComputationBlock(
        QubitHorizontalBorders(dimension),
        TemporalPlaquetteSequence(
            initial_plaquettes, repeating_plaquettes, final_plaquettes
        ),
    )


def xzo_block(dimension: LinearFunction) -> StandardComputationBlock:
    xzz = xzz_block(dimension)
    xzz.repeating_plaquettes = None
    return xzz


def zxo_block(dimension: LinearFunction) -> StandardComputationBlock:
    zxz = zxz_block(dimension)
    zxz.repeating_plaquettes = None
    return zxz
