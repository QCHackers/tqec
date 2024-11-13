"""Defines the data structures to represent the logical computations.

This module provides high-level abstractions to represent the fault-tolerant logical
computations protected by surface code. There are two representations of the logical
computation:

- :py:class:`~tqec.computation.zx_graph.ZXGraph`: A restricted form of the ZX diagram from
  the ZX-calculus.
- :py:class:`~tqec.computation.block_graph.BlockGraph`: A graph consisting of individual
  building blocks that fully specify the boundary conditions and topological structures
  of the logical computation. It corresponds to the commonly used 3D spacetime diagram
  representation of a surface code logical computation.
"""

from .zx_graph import ZXKind, ZXEdge, ZXGraph, ZXNode
from .cube import Cube, CubeKind, ZXCube, Port, YCube
from .pipe import Pipe, PipeKind
from .block_graph import BlockGraph
from .abstract_observable import AbstractObservable
from .conversion import convert_block_graph_to_zx_graph, convert_zx_graph_to_block_graph
from .correlation import CorrelationSurface, find_correlation_surfaces
from .zx_plot import plot_zx_graph, draw_zx_graph_on, draw_correlation_surface_on
