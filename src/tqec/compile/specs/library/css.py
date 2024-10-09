from collections import defaultdict
from functools import partial
from typing import Literal, cast

from tqec.compile.block import CompiledBlock
from tqec.compile.specs.base import CubeSpec, SpecRule
from tqec.plaquette.enums import MeasurementBasis, PlaquetteOrientation, ResetBasis
from tqec.plaquette.library.css import make_css_surface_code_plaquette
from tqec.plaquette.library.empty import empty_square_plaquette
from tqec.plaquette.plaquette import Plaquettes, RepeatedPlaquettes
from tqec.scale import LinearFunction
from tqec.templates.qubit import QubitTemplate

_DEFAULT_BLOCK_REPETITIONS = LinearFunction(2, -1)


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


CSS_SPEC_RULES: defaultdict[CubeSpec, SpecRule] = defaultdict(lambda: default_spec_rule)
