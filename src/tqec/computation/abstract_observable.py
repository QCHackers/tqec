"""Defines the :py:class:`~tqec.computation.AbstractObservable` class."""

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
    """An abstract description of a logical observable in the
    :py:class:`~tqec.computation.BlockGraph`.

    A logical observable corresponds to a `OBSERVABLE_INCLUDE <https://github.com/quantumlib/Stim/blob/main/doc/gates.md#OBSERVABLE_INCLUDE>`_
    instruction in the ``stim`` circuit and is composed of a set of measurements. Abstract observable specifies where are the measurements
    located in the block graph.

    Attributes:
        top_lines: A set of cubes and pipes of which a line of measurements on the top face should be included
            in the observable.
        bottom_regions: A set of pipes of which a region of stabilizer measurements on the bottom face should be included
            in the observable.
    """

    top_lines: frozenset[Cube | Pipe]
    bottom_regions: frozenset[Pipe]

    def __post_init__(self) -> None:
        if not self.top_lines and not self.bottom_regions:
            raise TQECException(
                "The top lines and bottom regions cannot both be empty."
            )


def correlation_surface_to_abstract_observable(
    block_graph: BlockGraph,
    correlation_surface: CorrelationSurface,
) -> AbstractObservable:
    """Convert a :py:class:`~tqec.computation.CorrelationSurface` to an
    :py:class:`~tqec.computation.AbstractObservable`.

    .. warning::
        It is assumed that the corresponding ZX graph of the block graph can support the correlation surface.
        Otherwise, the behavior is undefined.

    Args:
        block_graph: The block graph whose corresponding ZX graph supports the correlation surface.
        correlation_surface: The correlation surface to convert to an abstract observable.

    Returns:
        The abstract observable corresponding to the correlation surface in the block graph.

    Raises:
        TQECException: If the block graph has open ports.
    """
    if block_graph.num_ports != 0:
        raise TQECException(
            "The block graph must have no open ports to support observables."
        )
    if correlation_surface.has_single_node:
        return AbstractObservable(
            frozenset(block_graph.nodes),
            frozenset(),
        )

    def has_obs_include(cube: Cube, correlation: ZXKind) -> bool:
        if cube.is_y_cube:
            return True
        assert isinstance(cube.kind, ZXCube)
        # No pipe at the top
        if block_graph.has_edge_between(cube.position, cube.position.shift_by(0, 0, 1)):
            return False
        # The correlation surface must be attached to the top face
        return cube.kind.z.value == correlation.value

    top_lines: set[Cube | Pipe] = set()
    bottom_regions: set[Pipe] = set()
    for edge in correlation_surface.span:
        pipe = block_graph.get_edge(edge.u.position, edge.v.position)
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
