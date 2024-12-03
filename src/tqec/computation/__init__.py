"""Define the main data structures to represent the logical computation.

Under the context of topological quantum error correction, the logical computations
can be represented by the spacetime defect diagrams. The topological structure of the
spacetime diagram guides the computation and implements the desired logical subroutines.

This package defines the two main graph data structure to represent the spacetime diagram
of the logical computation:

- The :class:`ZXGraph` is in the form of a ZX-calculus graph and the representation is
  based on the correspondence between the ZX-calculus and the lattice surgery.
- The :class:`BlockGraph` specifies the explicit block structures of the spacetime diagram,
  including the layout of the code patches, the boundary types and the connectivity of the
  patches across the spacetime. The block graph can be compiled and used to generate the
  concrete circuits that implement the logical computation.
"""

from tqec.computation.block_graph import BlockGraph as BlockGraph
from tqec.computation.block_graph import BlockKind as BlockKind
from tqec.computation.cube import Cube as Cube
from tqec.computation.cube import CubeKind as CubeKind
from tqec.computation.cube import Port as Port
from tqec.computation.cube import YCube as YCube
from tqec.computation.cube import ZXCube as ZXCube
from tqec.computation.pipe import Pipe as Pipe
from tqec.computation.pipe import PipeKind as PipeKind
from tqec.computation.zx_graph import ZXEdge as ZXEdge
from tqec.computation.zx_graph import ZXGraph as ZXGraph
from tqec.computation.zx_graph import ZXKind as ZXKind
from tqec.computation.zx_graph import ZXNode as ZXNode
