import cirq

from tqec.circuit.operations.measurement import Measurement
from tqec.circuit.operations.operation import make_observable
from tqec.exceptions import TQECException
from tqec.position import Direction3D
from tqec.sketchup.block_graph import AbstractObservable, Cube, Pipe
from tqec.templates.scale import round_or_fail


def get_center_qubit_at_horizontal_pipe(pipe: Pipe, block_size: int) -> cirq.GridQubit:
    """Get the single center qubit of a horizontal pipe."""
    if pipe.direction == Direction3D.Z:
        raise TQECException("Can only get center qubit for horizontal pipes.")

    u_pos = pipe.u.position
    if pipe.direction == Direction3D.X:
        return cirq.GridQubit(
            round_or_fail((0.5 + u_pos.y) * block_size) - 1,
            (1 + u_pos.x) * block_size - 1,
        )
    else:
        return cirq.GridQubit(
            (1 + u_pos.y) * block_size - 1,
            round_or_fail((0.5 + u_pos.x) * block_size) - 1,
        )


def get_midline_qubits_for_cube(
    cube: Cube,
    block_size: int,
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
    pos = cube.position
    if midline_orientation == Direction3D.X:
        return [
            cirq.GridQubit(
                round_or_fail((0.5 + pos.y) * block_size) - 1,
                col,
            )
            for col in range(pos.x * block_size + 1, (pos.x + 1) * block_size - 1, 2)
        ]
    else:
        return [
            cirq.GridQubit(
                row,
                round_or_fail((0.5 + pos.x) * block_size) - 1,
            )
            for row in range(pos.y * block_size + 1, (pos.y + 1) * block_size - 1, 2)
        ]


def get_stabilizer_region_qubits_for_pipe(
    pipe: Pipe,
    block_size: int,
) -> list[cirq.GridQubit]:
    stabilizer_qubits: list[cirq.GridQubit] = []
    if pipe.pipe_type.direction == Direction3D.Z:
        raise TQECException(
            "Can only get stabilizer region qubits for horizontal pipes."
        )

    u_pos = pipe.u.position
    half_region_size = block_size // 4
    if pipe.pipe_type.direction == Direction3D.X:
        block_border_x = (u_pos.x + 1) * block_size - 1
        for i in range(half_region_size):
            x1 = block_border_x - 2 * i - 1
            x2 = block_border_x + 2 * i + 1
            for j in range(half_region_size):
                y1 = (2 - 2 * (i % 2)) + 4 * j + u_pos.y * block_size
                y2 = 2 * (i % 2) + 4 * j + u_pos.y * block_size
                stabilizer_qubits.append(cirq.GridQubit(y1, x1))
                stabilizer_qubits.append(cirq.GridQubit(y2, x2))
    else:
        block_border_y = (u_pos.y + 1) * block_size - 1
        for j in range(half_region_size):
            y1 = block_border_y - 2 * j - 1
            y2 = block_border_y + 2 * j + 1
            for i in range(half_region_size):
                x1 = 2 * (j % 2) + 4 * i + u_pos.x * block_size
                x2 = (2 - 2 * (j % 2)) + 4 * i + u_pos.x * block_size
                stabilizer_qubits.append(cirq.GridQubit(y1, x1))
                stabilizer_qubits.append(cirq.GridQubit(y2, x2))
    return stabilizer_qubits


def inplace_add_observables(
    circuits: list[list[cirq.Circuit]],
    abstract_observables: list[AbstractObservable],
    block_size: int,
) -> None:
    """Inplace add the observable components to the circuits.

    The circuits are grouped by time slices and layers. The outer list
    represents the time slices and the inner list represents the layers.
    """
    for i, observable in enumerate(abstract_observables):
        # Add the stabilizer region measurements to the end of the first layer of circuits at z.
        for pipe in observable.bottom_regions:
            z = pipe.u.position.z
            stabilizer_qubits = get_stabilizer_region_qubits_for_pipe(pipe, block_size)
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
                qubits = get_midline_qubits_for_cube(cube_or_pipe, block_size)
                z = cube_or_pipe.position.z
            else:
                qubits = [get_center_qubit_at_horizontal_pipe(cube_or_pipe, block_size)]
                z = cube_or_pipe.u.position.z
            observables = [
                make_observable(
                    measurements=[Measurement(q, -1) for q in qubits],
                    observable_index=i,
                )
            ]
            circuits[z][-1].append(observables, cirq.InsertStrategy.INLINE)
