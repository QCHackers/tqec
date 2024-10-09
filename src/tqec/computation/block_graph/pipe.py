from __future__ import annotations

from dataclasses import dataclass

from tqec.exceptions import TQECException
from tqec.position import Direction3D
from tqec.computation.block_graph.cube import Cube
from tqec.computation.block_graph.enums import PipeType


@dataclass(frozen=True)
class Pipe:
    """A block connecting two cubes in a 3D spacetime diagram.

    The pipe represents the idle or merge/split lattice surgery
    operation on logical qubits depending on its direction.
    """

    u: Cube
    v: Cube
    pipe_type: PipeType

    def __post_init__(self) -> None:
        if not self.u.position.is_neighbour(self.v.position):
            raise TQECException("A pipe must connect two nearby cubes.")
        # Ensure position of u is less than v
        u, v = self.u, self.v
        if self.u.position > self.v.position:
            object.__setattr__(self, "u", v)
            object.__setattr__(self, "v", u)

    @property
    def direction(self) -> Direction3D:
        """Get the direction of the pipe."""
        return self.pipe_type.direction
