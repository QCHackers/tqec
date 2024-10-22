from dataclasses import dataclass

from tqec.computation.cube import Cube, ZXCube
from tqec.computation.block_graph import BlockGraph
from tqec.computation.pipe import Pipe
from tqec.computation.correlation import CorrelationSurface
from tqec.computation.zx_graph import ZXKind
from tqec.exceptions import TQECException
from tqec.position import Direction3D


@dataclass(frozen=True)
class AbstractObservable:
    """An abstract description of an observable in a 3D spacetime diagram.

    In a **closed** 3D spacetime diagram, the abstract observable can be derived from
    the corresponding correlation surface:
    1. When the correlation surface attaches to the top/bottom faces of a block in
    the diagram, the measurements of the line of qubits on the top face are included
    in the observable.
    2. When the correlation surface lies within XY plane and intersects a pipe, the stabilizer
    measurements at the start of the pipe and part of the stabilizer measurements within
    the cubes connected by the pipe are included in the observable.
    """

    top_lines: frozenset[Cube | Pipe]
    bottom_regions: frozenset[Pipe]


def correlation_surface_to_abstract_observable(
    block_graph: BlockGraph,
    correlation_surface: CorrelationSurface,
    validate_graph: bool = True,
) -> AbstractObservable:
    """Convert a correlation surface to an abstract observable."""
    if validate_graph:
        if block_graph.num_ports != 0:
            raise TQECException(
                "The block graph must have not open ports to support observables."
            )
        block_graph.validate()

    def has_obs_include(cube: Cube, correlation: ZXKind) -> bool:
        if cube.is_y_cube:
            return True
        assert isinstance(cube.kind, ZXCube)
        # No pipe at the top
        if block_graph.has_pipe_between(cube.position, cube.position.shift_by(0, 0, 1)):
            return False
        # The correlation surface must be attached to the top face
        return cube.kind.z.value == correlation.value

    top_lines: set[Cube | Pipe] = set()
    bottom_regions: set[Pipe] = set()
    for edge in correlation_surface.span:
        pipe = block_graph.get_pipe(edge.u.position, edge.v.position)
        if pipe.direction == Direction3D.Z:
            if has_obs_include(pipe.v, edge.v.kind):
                top_lines.add(pipe.v)
            continue
        pipe_top_face = pipe.kind.z
        assert pipe_top_face is not None, "The pipe is guaranteed to be spatial."
        # There is correlation surface attached to the top of the pipe
        if pipe_top_face.value == edge.u.kind.value:
            top_lines.add(pipe)
            for cube, node in zip(pipe, edge):
                if has_obs_include(cube, node.kind):
                    top_lines.add(cube)
        else:
            bottom_regions.add(pipe)
    return AbstractObservable(frozenset(top_lines), frozenset(bottom_regions))
