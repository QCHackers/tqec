from typing import Literal, cast

from tqec.compile.block import CompiledBlock
from tqec.compile.specs.base import CubeSpec, PipeSpec, Substitution
from tqec.plaquette.enums import (
    MeasurementBasis,
    PlaquetteOrientation,
    PlaquetteSide,
    ResetBasis,
)
from tqec.plaquette.frozendefaultdict import FrozenDefaultDict
from tqec.plaquette.library import empty_square_plaquette, PlaquetteBuilder
from tqec.plaquette.plaquette import Plaquette, Plaquettes
from tqec.position import Direction3D
from tqec.scale import LinearFunction
from tqec.templates.qubit import QubitTemplate

_DEFAULT_BLOCK_REPETITIONS = LinearFunction(2, -1)


def _build_regular_plaquette(
    builder: PlaquetteBuilder,
    x_boundary_orientation: Literal["VERTICAL", "HORIZONTAL"],
    temporal_basis: Literal["X", "Z"] | None = None,
    data_init: bool = False,
    data_meas: bool = False,
    init_meas_only_on_side: PlaquetteSide | None = None,
) -> tuple[Plaquette, Plaquette]:
    b1, b2 = ("X", "Z") if x_boundary_orientation == "VERTICAL" else ("Z", "X")
    b1 = cast(Literal["X", "Z"], b1)
    b2 = cast(Literal["X", "Z"], b2)

    def factory(b: Literal["X", "Z"]) -> Plaquette:
        return builder(
            basis=b,
            data_initialization=ResetBasis(temporal_basis) if data_init else None,
            data_measurement=MeasurementBasis(temporal_basis) if data_meas else None,
            x_boundary_orientation=x_boundary_orientation,
            init_meas_only_on_side=init_meas_only_on_side,
        )

    return factory(b1), factory(b2)


def _build_regular_plaquettes(
    builder: PlaquetteBuilder,
    x_boundary_orientation: Literal["VERTICAL", "HORIZONTAL"],
    temporal_basis: Literal["X", "Z"] | None = None,
    data_initialization: bool = False,
    data_measurement: bool = False,
    init_meas_only_on_side: PlaquetteSide | None = None,
    repetitions: LinearFunction | None = None,
) -> Plaquettes:
    p1, p2 = _build_regular_plaquette(
        builder,
        x_boundary_orientation,
        temporal_basis,
        data_initialization,
        data_measurement,
        init_meas_only_on_side,
    )
    plaquettes = Plaquettes(
        FrozenDefaultDict(
            {
                6: p1.project_on_boundary(PlaquetteOrientation.UP),
                7: p2.project_on_boundary(PlaquetteOrientation.LEFT),
                9: p1,
                10: p2,
                12: p2.project_on_boundary(PlaquetteOrientation.RIGHT),
                13: p1.project_on_boundary(PlaquetteOrientation.DOWN),
            },
            default_factory=empty_square_plaquette,
        )
    )
    if repetitions is not None:
        plaquettes = plaquettes.repeat(repetitions)
    return plaquettes


def regular_block(
    builder: PlaquetteBuilder,
    temporal_basis: Literal["X", "Z"],
    x_boundary_orientation: Literal["VERTICAL", "HORIZONTAL"],
    number_of_repetitions: LinearFunction = _DEFAULT_BLOCK_REPETITIONS,
) -> CompiledBlock:
    initial_plaquettes = _build_regular_plaquettes(
        builder,
        x_boundary_orientation,
        temporal_basis,
        True,
        False,
    )
    repeating_plaquettes = _build_regular_plaquettes(
        builder,
        x_boundary_orientation,
        repetitions=number_of_repetitions,
    )
    final_plaquettes = _build_regular_plaquettes(
        builder,
        x_boundary_orientation,
        temporal_basis,
        False,
        True,
    )
    return CompiledBlock(
        template=QubitTemplate(),
        layers=[initial_plaquettes, repeating_plaquettes, final_plaquettes],
    )


def default_compiled_block_builder(
    spec: CubeSpec, *, plaquette_builder: PlaquetteBuilder
) -> CompiledBlock:
    """Default rule for generating a `CompiledBlock` based on a `CubeSpec`."""
    if spec.cube_type.is_regular:
        return regular_block(
            plaquette_builder,
            cast(Literal["X", "Z"], spec.cube_type.temporal_basis),
            _get_x_boundary_orientation(spec),
        )
    raise NotImplementedError("Irregular cubes are not implemented yet.")


def default_substitution_builder(
    pipe_spec: PipeSpec, *, plaquette_builder: PlaquetteBuilder
) -> Substitution:
    pipe_type = pipe_spec.pipe_type
    if pipe_type.has_hadamard:
        raise NotImplementedError("Hadamard pipes are not implemented yet.")
    # pipe in time direction
    if pipe_type.direction == Direction3D.Z:
        return _build_substitution_in_time_direction(pipe_spec, plaquette_builder)
    # pipe in space
    return _build_substitution_in_space(pipe_spec, plaquette_builder)


def _build_substitution_in_time_direction(
    pipe_spec: PipeSpec, plaquette_builder: PlaquetteBuilder
) -> Substitution:
    # substitute the final layer of the src block
    src = {
        -1: _build_regular_plaquettes(
            plaquette_builder,
            _get_x_boundary_orientation(pipe_spec.spec1),
        )
    }
    # substitute the first layer of the dst block
    dst = {
        0: _build_regular_plaquettes(
            plaquette_builder,
            _get_x_boundary_orientation(pipe_spec.spec2),
        )
    }
    return Substitution(src, dst)


def _build_substitution_plaquettes(
    builder: PlaquetteBuilder,
    substitution_side: PlaquetteSide,
    x_boundary_orientation: Literal["VERTICAL", "HORIZONTAL"],
    temporal_basis: Literal["X", "Z"] | None = None,
    data_initialization: bool = False,
    data_measurement: bool = False,
    repetitions: LinearFunction | None = None,
) -> Plaquettes:
    p1, p2 = _build_regular_plaquette(
        builder,
        x_boundary_orientation,
        temporal_basis,
        data_initialization,
        data_measurement,
        init_meas_only_on_side=substitution_side,
    )
    p3, p4 = _build_regular_plaquette(
        builder,
        x_boundary_orientation,
        temporal_basis,
    )
    mapping: dict[int, Plaquette]
    if substitution_side == PlaquetteSide.LEFT:
        mapping = {
            1: p3.project_on_boundary(PlaquetteOrientation.UP),
            7: p2,
            8: p3,
        }
    elif substitution_side == PlaquetteSide.UP:
        mapping = {
            2: p4.project_on_boundary(PlaquetteOrientation.RIGHT),
            5: p4,
            6: p1,
        }
    elif substitution_side == PlaquetteSide.RIGHT:
        mapping = {
            4: p3.project_on_boundary(PlaquetteOrientation.DOWN),
            11: p3,
            12: p2,
        }
    else:  # substitution_side == PlaquetteSide.DOWN
        mapping = {
            3: p4.project_on_boundary(PlaquetteOrientation.LEFT),
            13: p1,
            14: p4,
        }
    plaquettes = Plaquettes(
        FrozenDefaultDict(
            mapping,
            default_factory=empty_square_plaquette,
        )
    )
    if repetitions is not None:
        plaquettes = plaquettes.repeat(repetitions)
    return plaquettes


def _build_substitution_in_space(
    pipe_spec: PipeSpec,
    plaquette_builder: PlaquetteBuilder,
) -> Substitution:
    if pipe_spec.spec1.cube_type.is_regular and pipe_spec.spec2.cube_type.is_regular:
        return _build_substitution_in_space_with_regular_cubes(
            pipe_spec, plaquette_builder
        )
    raise NotImplementedError("Pipes between irregular cubes are not implemented yet.")


def _build_substitution_in_space_with_regular_cubes(
    pipe_spec: PipeSpec,
    plaquette_builder: PlaquetteBuilder,
) -> Substitution:
    pipe_type = pipe_spec.pipe_type
    temporal_basis = pipe_type.temporal_basis()
    # No hadamard: the two cubes have the same orientation
    orientation = _get_x_boundary_orientation(pipe_spec.spec1)
    # In `tqec` library, the positive y-axis is the downward direction
    substitute_side1 = (
        PlaquetteSide.RIGHT
        if pipe_spec.pipe_type.direction == Direction3D.X
        else PlaquetteSide.DOWN
    )
    substitute_side2 = substitute_side1.opposite()

    def build_substitution(side: PlaquetteSide) -> dict[int, Plaquettes]:
        return {
            0: _build_substitution_plaquettes(
                plaquette_builder, side, orientation, temporal_basis, True
            ),
            1: _build_substitution_plaquettes(
                plaquette_builder,
                side,
                orientation,
                repetitions=_DEFAULT_BLOCK_REPETITIONS,
            ),
            2: _build_substitution_plaquettes(
                plaquette_builder, side, orientation, temporal_basis, False, True
            ),
        }

    return Substitution(
        src=build_substitution(substitute_side1),
        dst=build_substitution(substitute_side2),
    )


def _get_x_boundary_orientation(
    cube_spec: CubeSpec,
) -> Literal["VERTICAL", "HORIZONTAL"]:
    cube_type = cube_spec.cube_type.value
    return "VERTICAL" if cube_type[0] == "z" else "HORIZONTAL"
