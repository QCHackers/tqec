"""Regression tests for parity cancellation of same-cube top readouts (#1155)."""

from tqec.circuit.qubit import GridQubit
from tqec.compile.observables.abstract_observable import AbstractObservable, CubeWithArms
from tqec.compile.observables.builder import ObservableComponent
from tqec.compile.observables.fixed_bulk_builder import FIXED_BULK_OBSERVABLE_BUILDER
from tqec.compile.specs.enums import SpatialArms
from tqec.computation.cube import Cube, ZXCube
from tqec.templates.layout import LayoutTemplate
from tqec.templates.qubit import QubitTemplate
from tqec.utils.position import BlockPosition2D, Position3D


def test_same_cube_top_readout_contributions_cancel_modulo_two() -> None:
    """Count a shared center measurement twice as zero in the logical parity."""
    cube = Cube(Position3D(0, 0, 0), ZXCube.from_str("ZZX"))
    left_down = CubeWithArms(cube, SpatialArms.LEFT | SpatialArms.DOWN)
    right_up = CubeWithArms(cube, SpatialArms.RIGHT | SpatialArms.UP)
    template = LayoutTemplate({BlockPosition2D(0, 0): QubitTemplate()})

    def readout(*parts: CubeWithArms) -> set[GridQubit]:
        return FIXED_BULK_OBSERVABLE_BUILDER.build(
            1,
            template,
            AbstractObservable(top_readout_cubes=frozenset(parts)),
            ObservableComponent.TOP_READOUTS,
        )

    a = readout(left_down)
    b = readout(right_up)
    combined = readout(left_down, right_up)

    assert a & b == {GridQubit(3, 3)}
    assert combined == a ^ b
    assert combined == {
        GridQubit(1, 3),
        GridQubit(3, 1),
        GridQubit(3, 5),
        GridQubit(5, 3),
    }
