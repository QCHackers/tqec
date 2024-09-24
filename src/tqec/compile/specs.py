from typing import Protocol, Literal
from dataclasses import dataclass
from collections import defaultdict

from tqec.plaquette.plaquette import Plaquettes, RepeatedPlaquettes
from tqec.compile.block import CompiledBlock
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
from tqec.sketchup.block_graph import BlockGraph, Cube, CubeType
from tqec.templates.qubit import QubitTemplate
from tqec.templates.scale import LinearFunction

# NOTE: Need to change this to LinearFunction(2, -1), refer to Issue#320
_DEFAULT_BLOCK_REPETITIONS = LinearFunction(2, 1)


@dataclass(frozen=True)
class CubeSpec:
    """Specification of a cube in a block graph.

    The template of the `CompiledBlock` will be determined based on the specification.
    This class can be used as a key to look up the corresponding `CompiledBlock` before
    applying the substitution rules.

    Attributes:
        cube_type: Type of the cube.
        arm_flags: Flags indicating whether the cube connects to the adjacent cubes.
            The flags are in the order of [up, right, down, left]. This is useful for
            spatial junctions (XXZ and ZZX) where the arms can determine the template
            used to implement the cube.
    """

    cube_type: CubeType
    arm_flags: tuple[bool, bool, bool, bool] | None = None

    def __post_init__(self) -> None:
        # arm_flags is not None iff cube_type is ZZX or XXZ(Spatial Junctions)
        if (self.is_spatial_junction) ^ (self.arm_flags is not None):
            raise TQECException(
                "arm_flags is not None if and only if cube_type is spatial junctions(ZZX or XXZ)."
            )

    @property
    def is_spatial_junction(self) -> bool:
        return self.cube_type.is_spatial_junction

    @staticmethod
    def from_cube(cube: Cube, graph: BlockGraph) -> "CubeSpec":
        """Returns the cube spec from a cube in a block graph."""
        if cube.cube_type not in [CubeType.ZZX, CubeType.XXZ]:
            return CubeSpec(cube.cube_type)
        pos = cube.position
        arm_flags = (
            graph.get_pipe(pos, pos.shift_by(dy=1)) is not None,
            graph.get_pipe(pos, pos.shift_by(dx=1)) is not None,
            graph.get_pipe(pos, pos.shift_by(dy=-1)) is not None,
            graph.get_pipe(pos, pos.shift_by(dx=-1)) is not None,
        )
        return CubeSpec(cube.cube_type, arm_flags)


class SpecRule(Protocol):
    def __call__(self, spec: CubeSpec) -> CompiledBlock:
        """Protocol for returning a `CompiledBlock` based on a `CubeSpec`.

        Users can define their own rules for generating `CompiledBlock`s based on the
        `CubeSpec` provided and register them during the compilation process.

        Args:
            spec: Specification of the cube in the block graph.

        Returns:
            a `CompiledBlock` based on the provided `CubeSpec`.
        """
        ...


def _zxB_block(basis: Literal["X", "Z"]) -> CompiledBlock:
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
        defaultdict(empty_square_plaquette)
        | {
            6: xx_memory_plaquette(PlaquetteOrientation.UP),
            7: zz_memory_plaquette(PlaquetteOrientation.LEFT),
            9: xxxx_memory_plaquette(),
            10: zzzz_memory_plaquette(),
            12: zz_memory_plaquette(PlaquetteOrientation.RIGHT),
            13: xx_memory_plaquette(PlaquetteOrientation.DOWN),
        },
        _DEFAULT_BLOCK_REPETITIONS,
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
    return CompiledBlock(
        template=QubitTemplate(),
        layers=[initial_plaquettes, repeating_plaquettes, final_plaquettes],
    )


def _xzB_block(basis: Literal["X", "Z"]) -> CompiledBlock:
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
        defaultdict(empty_square_plaquette)
        | {
            6: zz_memory_plaquette(PlaquetteOrientation.UP),
            7: xx_memory_plaquette(PlaquetteOrientation.LEFT),
            9: zzzz_memory_plaquette(),
            10: xxxx_memory_plaquette(),
            12: xx_memory_plaquette(PlaquetteOrientation.RIGHT),
            13: zz_memory_plaquette(PlaquetteOrientation.DOWN),
        },
        _DEFAULT_BLOCK_REPETITIONS,
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
    return CompiledBlock(
        template=QubitTemplate(),
        layers=[initial_plaquettes, repeating_plaquettes, final_plaquettes],
    )


def default_spec_rule(spec: CubeSpec) -> CompiledBlock:
    """Default rule for generating a `CompiledBlock` based on a `CubeSpec`."""
    match spec.cube_type, spec.arm_flags:
        case CubeType.ZXZ, None:
            return _zxB_block("Z")
        case CubeType.ZXX, None:
            return _zxB_block("X")
        case CubeType.XZZ, None:
            return _xzB_block("Z")
        case CubeType.XZX, None:
            return _xzB_block("X")
        case CubeType.ZZX | CubeType.XXZ, _arm_flags:
            raise NotImplementedError("Spatial junctions are not implemented yet.")
        case _:
            raise TQECException(f"Unsupported cube spec: {spec}")


DEFAULT_SPEC_RULES: defaultdict[CubeSpec, SpecRule] = defaultdict(
    lambda: default_spec_rule
)
