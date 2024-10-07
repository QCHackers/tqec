from dataclasses import dataclass

from tqec.sketchup.block_graph.cube import Cube
from tqec.sketchup.block_graph.pipe import Pipe


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
