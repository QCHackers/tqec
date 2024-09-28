import cirq

from tqec.circuit.operations.measurement import Measurement
from tqec.circuit.operations.operation import make_observable
from tqec.exceptions import TQECException
from tqec.position import Direction3D, Displacement, Shape2D
from tqec.sketchup.block_graph import AbstractObservable, Cube, Pipe
from tqec.templates.layout import LayoutTemplate
from tqec.templates.scale import round_or_fail


def get_center_qubit_at_horizontal_pipe(
    pipe: Pipe, block_shape: Shape2D, template_increments: Displacement
) -> cirq.GridQubit:
    """Get the single center qubit of a horizontal pipe."""
    if pipe.direction == Direction3D.Z:
        raise TQECException("Can only get center qubit for horizontal pipes.")

    width = block_shape.x * template_increments.x
    height = block_shape.y * template_increments.y
    half_increment_x = template_increments.x // 2
    half_increment_y = template_increments.y // 2
    u_pos = pipe.u.position
    if pipe.direction == Direction3D.X:
        return cirq.GridQubit(
            round_or_fail((0.5 + u_pos.y) * height) - half_increment_y,
            (1 + u_pos.x) * width - half_increment_x,
        )
    else:
        return cirq.GridQubit(
            (1 + u_pos.y) * height - 1,
            round_or_fail((0.5 + u_pos.x) * width) - 1,
        )


def get_midline_qubits_for_cube(
    cube: Cube, block_shape: Shape2D, template_increments: Displacement
) -> list[cirq.GridQubit]:
    """Get the midline qubits for a cube."""
    if cube.cube_type.is_spatial_junction or cube.is_virtual:
        raise TQECException(
            "Cannot get midline qubits for a spatial junction cube or a virtual cube."
        )
    cube_type = cube.cube_type.value
    time_boundary_basis = cube_type[2]
    midline_orientation = Direction3D.from_axis_index(
        cube_type.index(time_boundary_basis)
    )
    assert midline_orientation != Direction3D.Z

    width = block_shape.x * template_increments.x
    height = block_shape.y * template_increments.y
    half_increment_x = template_increments.x // 2
    half_increment_y = template_increments.y // 2
    pos = cube.position
    if midline_orientation == Direction3D.X:
        return [
            cirq.GridQubit(
                round_or_fail((0.5 + pos.y) * height) - half_increment_y,
                col,
            )
            for col in range(
                pos.x * width + half_increment_x,
                (pos.x + 1) * width - half_increment_x,
                template_increments.x,
            )
        ]
    else:
        return [
            cirq.GridQubit(
                row,
                round_or_fail((0.5 + pos.x) * width) - half_increment_x,
            )
            for row in range(
                pos.y * height + half_increment_y,
                (pos.y + 1) * height - half_increment_y,
                template_increments.y,
            )
        ]


def get_stabilizer_region_qubits_for_pipe(
    pipe: Pipe,
    block_shape: Shape2D,
    template_increments: Displacement,
) -> list[cirq.GridQubit]:
    stabilizer_qubits: list[cirq.GridQubit] = []
    if pipe.pipe_type.direction == Direction3D.Z:
        raise TQECException(
            "Can only get stabilizer region qubits for horizontal pipes."
        )

    width = block_shape.x * template_increments.x
    height = block_shape.y * template_increments.y
    half_increment_x = template_increments.x // 2
    half_increment_y = template_increments.y // 2
    u_pos = pipe.u.position
    if pipe.pipe_type.direction == Direction3D.X:
        block_border_x = (u_pos.x + 1) * width - half_increment_x
        for i in range(block_shape.x // 2):
            x1 = block_border_x - template_increments.x * i - half_increment_x
            x2 = block_border_x + template_increments.x * i + half_increment_x
            for j in range(block_shape.y // 2):
                y1 = (
                    template_increments.y * (1 - i % 2)
                    + 2 * template_increments.y * j
                    + u_pos.y * height
                )
                y2 = (
                    template_increments.y * (i % 2)
                    + 2 * template_increments.y * j
                    + u_pos.y * height
                )
                stabilizer_qubits.append(cirq.GridQubit(y1, x1))
                stabilizer_qubits.append(cirq.GridQubit(y2, x2))
    else:
        block_border_y = (u_pos.y + 1) * height - 1
        for j in range(block_shape.y // 2):
            y1 = block_border_y - template_increments.y * j - half_increment_y
            y2 = block_border_y + template_increments.y * j + half_increment_y
            for i in range(block_shape.x // 2):
                x1 = (
                    template_increments.x * (j % 2)
                    + 2 * template_increments.x * i
                    + u_pos.x * width
                )
                x2 = (
                    template_increments.x * (1 - j % 2)
                    + 2 * template_increments.x * i
                    + u_pos.x * width
                )
                stabilizer_qubits.append(cirq.GridQubit(y1, x1))
                stabilizer_qubits.append(cirq.GridQubit(y2, x2))
    return stabilizer_qubits


def inplace_add_observables(
    circuits: list[list[cirq.Circuit]],
    template_slices: list[LayoutTemplate],
    abstract_observables: list[AbstractObservable],
) -> None:
    """Inplace add the observable components to the circuits.

    The circuits are grouped by time slices and layers. The outer list
    represents the time slices and the inner list represents the layers.
    """
    for i, observable in enumerate(abstract_observables):
        # Add the stabilizer region measurements to the end of the first layer of circuits at z.
        for pipe in observable.bottom_regions:
            z = pipe.u.position.z
            template = template_slices[z]
            stabilizer_qubits = get_stabilizer_region_qubits_for_pipe(
                pipe, template.element_shape, template.get_increments()
            )
            observables = [
                make_observable(
                    measurements=[Measurement(q, -1) for q in stabilizer_qubits],
                    observable_index=i,
                )
            ]
            circuits[z][0].append(observables, cirq.InsertStrategy.INLINE)
        # Add the line measurements to the end of the last layer of circuits at z.
        for cube_or_pipe in observable.top_lines:
            if isinstance(cube_or_pipe, Cube):
                z = cube_or_pipe.position.z
                template = template_slices[z]
                qubits = get_midline_qubits_for_cube(
                    cube_or_pipe, template.element_shape, template.get_increments()
                )
            else:
                z = cube_or_pipe.u.position.z
                template = template_slices[z]
                qubits = [
                    get_center_qubit_at_horizontal_pipe(
                        cube_or_pipe, template.element_shape, template.get_increments()
                    )
                ]
            observables = [
                make_observable(
                    measurements=[Measurement(q, -1) for q in qubits],
                    observable_index=i,
                )
            ]
            circuits[z][-1].append(observables, cirq.InsertStrategy.INLINE)
