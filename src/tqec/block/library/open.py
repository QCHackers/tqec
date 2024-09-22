from collections import defaultdict

import cirq

from tqec.block.block import (
    _DEFAULT_BLOCK_REPETITIONS,
    RepeatedPlaquettes,
    StandardComputationBlock,
    TemporalPlaquetteSequence,
)
from tqec.plaquette.enums import PlaquetteOrientation, PlaquetteSide
from tqec.plaquette.library.empty import empty_square_plaquette
from tqec.plaquette.library.memory import (
    xx_memory_plaquette,
    xxxx_memory_plaquette,
    zz_memory_plaquette,
    zzzz_memory_plaquette,
)
from tqec.plaquette.library.pauli import MeasurementBasis, ResetBasis
from tqec.plaquette.plaquette import Plaquette, Plaquettes
from tqec.templates.qubit import (
    QubitHorizontalBorders,
    QubitTemplate,
    QubitVerticalBorders,
)


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


def ozx_block() -> StandardComputationBlock:
    initial_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
            2: _with_resets_on_data_qubits_on_side(
                zzzz_memory_plaquette(),
                PlaquetteSide.RIGHT,
                reset_basis=ResetBasis.X,
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
    )
    repeating_plaquettes = RepeatedPlaquettes(
        Plaquettes(
            defaultdict(empty_square_plaquette)
            | {
                2: _with_resets_on_data_qubits_on_side(
                    zzzz_memory_plaquette(),
                    PlaquetteSide.RIGHT,
                    reset_basis=ResetBasis.X,
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
        ),
        _DEFAULT_BLOCK_REPETITIONS,
    )
    final_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
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
    )
    return StandardComputationBlock(
        QubitVerticalBorders(),
        TemporalPlaquetteSequence(
            initial_plaquettes, repeating_plaquettes, final_plaquettes
        ),
    )


def oxz_block() -> StandardComputationBlock:
    initial_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
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
    )
    repeating_plaquettes = RepeatedPlaquettes(
        Plaquettes(
            defaultdict(empty_square_plaquette)
            | {
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
        ),
        _DEFAULT_BLOCK_REPETITIONS,
    )
    final_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
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
    )
    return StandardComputationBlock(
        QubitVerticalBorders(),
        TemporalPlaquetteSequence(
            initial_plaquettes, repeating_plaquettes, final_plaquettes
        ),
    )


def xoz_block() -> StandardComputationBlock:
    initial_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
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
    )
    repeating_plaquettes = RepeatedPlaquettes(
        Plaquettes(
            defaultdict(empty_square_plaquette)
            | {
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
        ),
        _DEFAULT_BLOCK_REPETITIONS,
    )
    final_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
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
    )
    return StandardComputationBlock(
        QubitHorizontalBorders(),
        TemporalPlaquetteSequence(
            initial_plaquettes, repeating_plaquettes, final_plaquettes
        ),
    )


def zox_block() -> StandardComputationBlock:
    initial_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
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
    )
    repeating_plaquettes = RepeatedPlaquettes(
        Plaquettes(
            defaultdict(empty_square_plaquette)
            | {
                1: _with_resets_on_data_qubits_on_side(
                    zz_memory_plaquette(PlaquetteOrientation.LEFT),
                    PlaquetteSide.DOWN,
                    reset_basis=ResetBasis.X,
                ),
                2: xxxx_memory_plaquette(),
                3: _with_resets_on_data_qubits_on_side(
                    zzzz_memory_plaquette(),
                    PlaquetteSide.DOWN,
                    reset_basis=ResetBasis.X,
                ),
                6: zzzz_memory_plaquette(),
                7: xxxx_memory_plaquette(),
                8: zz_memory_plaquette(PlaquetteOrientation.RIGHT),
            }
        ),
        _DEFAULT_BLOCK_REPETITIONS,
    )
    final_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
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
    )
    return StandardComputationBlock(
        QubitHorizontalBorders(),
        TemporalPlaquetteSequence(
            initial_plaquettes, repeating_plaquettes, final_plaquettes
        ),
    )


def xzo_block() -> StandardComputationBlock:
    initial_plaquettes = final_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
            6: zz_memory_plaquette(PlaquetteOrientation.UP),
            7: xx_memory_plaquette(PlaquetteOrientation.LEFT),
            9: zzzz_memory_plaquette(),
            10: xxxx_memory_plaquette(),
            12: xx_memory_plaquette(PlaquetteOrientation.RIGHT),
            13: zz_memory_plaquette(PlaquetteOrientation.DOWN),
        }
    )
    return StandardComputationBlock(
        QubitTemplate(),
        TemporalPlaquetteSequence(initial_plaquettes, None, final_plaquettes),
    )


def zxo_block() -> StandardComputationBlock:
    initial_plaquettes = final_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
            6: xx_memory_plaquette(PlaquetteOrientation.UP),
            7: zz_memory_plaquette(PlaquetteOrientation.LEFT),
            9: xxxx_memory_plaquette(),
            10: zzzz_memory_plaquette(),
            12: zz_memory_plaquette(PlaquetteOrientation.RIGHT),
            13: xx_memory_plaquette(PlaquetteOrientation.DOWN),
        }
    )
    return StandardComputationBlock(
        QubitTemplate(),
        TemporalPlaquetteSequence(initial_plaquettes, None, final_plaquettes),
    )
