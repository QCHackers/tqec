from unittest.mock import Mock, patch

from tqec.circuit.qubit import GridQubit
from tqec.compile.observables.builder import ObservableBuilder, ObservableComponent
from tqec.templates.layout import LayoutTemplate
from tqec.templates.qubit import QubitTemplate
from tqec.utils.position import (
    BlockPosition2D,
    Position3D,
)


def test_transform_coords_into_grid() -> None:
    template = LayoutTemplate(
        {
            BlockPosition2D(0, 0): QubitTemplate(),
            BlockPosition2D(1, 0): QubitTemplate(),
            BlockPosition2D(1, 1): QubitTemplate(),
        }
    )
    qubits = ObservableBuilder.transform_coords_into_grid(
        5,
        template,
        local_coords=[(2, 2)],
        block_position=Position3D(1, 1, 0),
    )
    assert qubits == {GridQubit(27, 27)}

    qubits = ObservableBuilder.transform_coords_into_grid(
        12,
        template,
        local_coords=[(3, 1)],
        block_position=Position3D(0, 1, 0),
    )
    x = -1 + 3 * 2
    y = (12 * 2 + 2) * 2 - 1 + 1 * 2
    assert qubits == {GridQubit(x, y)}


def test_top_readouts_use_same_cube_parity_and_different_cube_union() -> None:
    """Cancel duplicates within a cube, then union results from distinct sources."""
    center = Position3D(0, 0, 0)
    neighbor = Position3D(1, 0, 0)

    first, second, third, pipe = Mock(), Mock(), Mock(), Mock()
    first.cube.position = second.cube.position = center
    third.cube.position = neighbor
    pipe.pipe.u.position = center
    first.coords = ((1, 1), (3, 3))
    second.coords = ((3, 3), (5, 5))
    third.coords = ((3, 3), (7, 7))
    pipe.coords = ((5, 5), (9, 9))

    builder = ObservableBuilder(
        cube_top_readouts_builder=lambda shape, cube: cube.coords,
        pipe_top_readouts_builder=lambda shape, pipe: pipe.coords,
        cube_bottom_stabilizers_builder=lambda shape, cube: (),
        pipe_bottom_stabilizers_builder=lambda shape, pipe: (),
        pipe_temporal_hadamard_builder=lambda shape, pipe: (),
    )
    template = Mock()

    def to_grid(_k, _template, coords, _pos):
        return {GridQubit(*xy) for xy in coords}

    with patch.object(ObservableBuilder, "transform_coords_into_grid", side_effect=to_grid):
        same_cube = builder.build(
            1,
            template,
            Mock(top_readout_cubes=(first, second), top_readout_pipes=()),
            ObservableComponent.TOP_READOUTS,
        )
        combined = builder.build(
            1,
            template,
            Mock(top_readout_cubes=(first, second, third), top_readout_pipes=(pipe,)),
            ObservableComponent.TOP_READOUTS,
        )

    assert same_cube == {GridQubit(1, 1), GridQubit(5, 5)}
    assert combined == {
        GridQubit(1, 1),
        GridQubit(3, 3),
        GridQubit(5, 5),
        GridQubit(7, 7),
        GridQubit(9, 9),
    }
