from functools import partial
from collections import defaultdict
from dataclasses import dataclass
from enum import Flag, auto
from typing import Protocol, Literal, cast

from tqec.plaquette.library.css import make_css_surface_code_plaquette
from tqec.plaquette.plaquette import Plaquettes, RepeatedPlaquettes
from tqec.compile.block import CompiledBlock
from tqec.exceptions import TQECException
from tqec.plaquette.enums import (
    PlaquetteOrientation,
    ResetBasis,
    MeasurementBasis,
)
from tqec.plaquette.library.empty import empty_square_plaquette
from tqec.scale import LinearFunction
from tqec.sketchup.block_graph import BlockGraph, Cube, CubeType
from tqec.templates.qubit import QubitTemplate

_DEFAULT_BLOCK_REPETITIONS = LinearFunction(2, -1)


class JunctionArms(Flag):
    NONE = 0
    UP = auto()
    RIGHT = auto()
    DOWN = auto()
    LEFT = auto()

    @classmethod
    def get_map_from_arm_to_shift(cls) -> dict["JunctionArms", tuple[int, int]]:
        return {
            cls.UP: (0, 1),
            cls.RIGHT: (1, 0),
            cls.DOWN: (0, -1),
            cls.LEFT: (-1, 0),
        }


@dataclass(frozen=True)
class CubeSpec:
    """Specification of a cube in a block graph.

    The template of the `CompiledBlock` will be determined based on the specification.
    This class can be used as a key to look up the corresponding `CompiledBlock` before
    applying the substitution rules.

    Attributes:
        cube_type: Type of the cube.
        junction_arms: Flag indicating the spatial directions the cube connects to the
            adjacent cubes. This is useful for spatial junctions (XXZ and ZZX) where
            the arms can determine the template used to implement the cube.
    """

    cube_type: CubeType
    junction_arms: JunctionArms = JunctionArms.NONE

    def __post_init__(self) -> None:
        # arm_flags is not None iff cube_type is ZZX or XXZ(Spatial Junctions)
        if (self.is_spatial_junction) ^ (self.junction_arms != JunctionArms.NONE):
            raise TQECException(
                "junction_arms is not NONE if and only if cube_type is spatial junctions(ZZX or XXZ)."
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
        junction_arms = JunctionArms.NONE
        for flag, shift in JunctionArms.get_map_from_arm_to_shift().items():
            if graph.get_pipe(pos, pos.shift_by(*shift)) is not None:
                junction_arms |= flag
        return CubeSpec(cube.cube_type, junction_arms)


class SpecRule(Protocol):
    """Protocol for returning a `CompiledBlock` based on a `CubeSpec`.

    Users can define their own rules for generating `CompiledBlock`s based on the
    `CubeSpec` provided and register them during compilation.
    """

    def __call__(self, spec: CubeSpec) -> CompiledBlock:
        """Get a `CompiledBlock` instance from a `CubeSpec`.

        Args:
            spec: Specification of the cube in the block graph.

        Returns:
            a `CompiledBlock` based on the provided `CubeSpec`.
        """
        ...


def _usual_block(
    basis: Literal["X", "Z"], x_boundary_orientation: Literal["VERTICAL", "HORIZONTAL"]
) -> CompiledBlock:
    reset_basis: ResetBasis = getattr(ResetBasis, basis)
    measurement_basis: MeasurementBasis = getattr(MeasurementBasis, basis)
    factory = partial(
        make_css_surface_code_plaquette,
        x_boundary_orientation=x_boundary_orientation,
    )
    b1, b2 = ("X", "Z") if x_boundary_orientation == "VERTICAL" else ("Z", "X")
    b1 = cast(Literal["X", "Z"], b1)
    b2 = cast(Literal["X", "Z"], b2)

    initial_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
            6: factory(b1, reset_basis).project_on_boundary(PlaquetteOrientation.UP),
            7: factory(b2, reset_basis).project_on_boundary(PlaquetteOrientation.LEFT),
            9: factory(b1, reset_basis),
            10: factory(b2, reset_basis),
            12: factory(b2, reset_basis).project_on_boundary(
                PlaquetteOrientation.RIGHT
            ),
            13: factory(b1, reset_basis).project_on_boundary(PlaquetteOrientation.DOWN),
        }
    )
    repeating_plaquettes = RepeatedPlaquettes(
        defaultdict(empty_square_plaquette)
        | {
            6: factory(b1).project_on_boundary(PlaquetteOrientation.UP),
            7: factory(b2).project_on_boundary(PlaquetteOrientation.LEFT),
            9: factory(b1),
            10: factory(b2),
            12: factory(b2).project_on_boundary(PlaquetteOrientation.RIGHT),
            13: factory(b1).project_on_boundary(PlaquetteOrientation.DOWN),
        },
        _DEFAULT_BLOCK_REPETITIONS,
    )
    final_plaquettes = Plaquettes(
        defaultdict(empty_square_plaquette)
        | {
            6: factory(b1, None, measurement_basis).project_on_boundary(
                PlaquetteOrientation.UP
            ),
            7: factory(b2, None, measurement_basis).project_on_boundary(
                PlaquetteOrientation.LEFT
            ),
            9: factory(b1, None, measurement_basis),
            10: factory(b2, None, measurement_basis),
            12: factory(b2, None, measurement_basis).project_on_boundary(
                PlaquetteOrientation.RIGHT
            ),
            13: factory(b1, None, measurement_basis).project_on_boundary(
                PlaquetteOrientation.DOWN
            ),
        }
    )
    return CompiledBlock(
        template=QubitTemplate(),
        layers=[initial_plaquettes, repeating_plaquettes, final_plaquettes],
    )


def default_spec_rule(spec: CubeSpec) -> CompiledBlock:
    """Default rule for generating a `CompiledBlock` based on a `CubeSpec`."""
    if spec.is_spatial_junction:
        raise NotImplementedError("Spatial junctions are not implemented yet.")
    cube_type = spec.cube_type.value
    x_boundary_orientation = "VERTICAL" if cube_type[0] == "z" else "HORIZONTAL"
    time_basis = cube_type[2].upper()
    return _usual_block(
        cast(Literal["X", "Z"], time_basis),
        cast(Literal["VERTICAL", "HORIZONTAL"], x_boundary_orientation),
    )


DEFAULT_SPEC_RULES: defaultdict[CubeSpec, SpecRule] = defaultdict(
    lambda: default_spec_rule
)
