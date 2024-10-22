from dataclasses import dataclass

from tqec.computation.block_graph.cube import Cube
from tqec.computation.block_graph.pipe import Pipe
from tqec.computation.correlation import CorrelationSurface
from tqec.computation.zx_graph import ZXKind, ZXNode
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


# def correlation_surface_to_abstract_observable(
#     block_graph: BlockGraph,
#     correlation_surface: CorrelationSurface,
#     validate_graph: bool = True,
# ) -> AbstractObservable:
#     """Convert a correlation surface to an abstract observable."""
#     if validate_graph:
#         if block_graph.num_ports != 0:
#             raise TQECException(
#                 "The block graph must not have open ports to support observables."
#             )
#         block_graph.validate()
#
#     if isinstance(correlation_surface.span, ZXNode):
#         return AbstractObservable(frozenset(block_graph.cubes), frozenset())
#
#     def has_obs_include(cube: Cube, correlation: ZXKind) -> bool:
#         # no_pipe_on_the_top
#         if block_graph.has_pipe_between(
#             cube.position, cube.position.shift_by(0, 0, 1)
#         ):
#             return False
#
#     top_lines: set[Cube | Pipe] = set()
#     bottom_regions: set[Pipe] = set()
#     for edge in correlation_surface.span:
#         correlation_at_head = edge.u.kind
#         correlation_at_tail = edge.v.kind
#         pipe = block_graph.get_pipe(edge.u.position, edge.v.position)
#         u, v = pipe.u, pipe.v
#         if pipe.direction == Direction3D.Z:
#             if has_obs_include(v) and v.kind. == correlation_at_tail:
#                 top_lines.add(v)
#             continue
#         # The direction for which the correlation surface of that type
#         # can be attached to the pipe
#         correlation_type_direction = Direction3D.from_axis_index(
#             pipe.pipe_type.value.index(correlation_at_head)
#         )
#         if correlation_type_direction == Direction3D.Z:
#             top_lines.add(pipe)
#             if has_obs_include(u):
#                 top_lines.add(u)
#             if has_obs_include(v):
#                 top_lines.add(v)
#         else:
#             bottom_regions.add(pipe)
#     abstract_observables.append(
#         AbstractObservable(frozenset(top_lines), frozenset(bottom_regions))
#     )
