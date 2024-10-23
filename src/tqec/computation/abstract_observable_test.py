from typing import Literal
import pytest

from tqec.computation.abstract_observable import AbstractObservable
from tqec.computation.block_graph import BlockGraph
from tqec.computation.cube import Cube, Port, YCube, ZXCube
from tqec.computation.pipe import PipeKind
from tqec.gallery.logical_cnot import logical_cnot_block_graph
from tqec.gallery.three_cnots import three_cnots_block_graph
from tqec.exceptions import TQECException
from tqec.position import Position3D


def test_abstract_observable_for_single_cube() -> None:
    g = BlockGraph()
    g.add_cube(Position3D(0, 0, 0), ZXCube.from_str("ZXZ"))
    observables, correlation_surfaces = g.get_abstract_observables()
    assert len(observables) == 1
    assert len(correlation_surfaces) == 0
    assert observables[0] == AbstractObservable(
        top_lines=frozenset({Cube(Position3D(0, 0, 0), ZXCube.from_str("ZXZ"))}),
        bottom_regions=frozenset(),
    )


def test_abstract_observable_open_ports() -> None:
    g = BlockGraph()
    g.add_pipe(
        Cube(Position3D(0, 0, 0), ZXCube.from_str("ZXZ")),
        Cube(Position3D(0, 0, 1), Port(), "open"),
        PipeKind.from_str("ZXO"),
    )
    with pytest.raises(
        TQECException,
        match="The block graph must have no open ports to support observables.",
    ):
        g.get_abstract_observables()


def test_abstract_observable_for_single_vertical_pipe() -> None:
    g = BlockGraph()
    g.add_pipe(
        Cube(Position3D(0, 0, 0), ZXCube.from_str("ZXZ")),
        Cube(Position3D(0, 0, 1), ZXCube.from_str("ZXZ")),
        PipeKind.from_str("ZXO"),
    )
    observables, correlation_surfaces = g.get_abstract_observables()
    assert len(observables) == len(correlation_surfaces) == 1
    assert observables[0] == AbstractObservable(
        top_lines=frozenset({Cube(Position3D(0, 0, 1), ZXCube.from_str("ZXZ"))}),
        bottom_regions=frozenset(),
    )


def test_abstract_observable_for_single_horizontal_pipe() -> None:
    g = BlockGraph()
    g.add_pipe(
        Cube(Position3D(0, 0, 0), ZXCube.from_str("ZXZ")),
        Cube(Position3D(1, 0, 0), ZXCube.from_str("ZXZ")),
        PipeKind.from_str("OXZ"),
    )
    observables, correlation_surfaces = g.get_abstract_observables()
    assert len(observables) == len(correlation_surfaces) == 1
    assert observables[0] == AbstractObservable(
        top_lines=frozenset(g.cubes + g.pipes),
        bottom_regions=frozenset(),
    )

    g = BlockGraph()
    g.add_pipe(
        Cube(Position3D(0, 0, 0), ZXCube.from_str("XXZ")),
        Cube(Position3D(1, 0, 0), ZXCube.from_str("XXZ")),
        PipeKind.from_str("OXZ"),
    )
    observables, correlation_surfaces = g.get_abstract_observables()
    assert len(observables) == len(correlation_surfaces) == 1
    assert observables[0] == AbstractObservable(
        top_lines=frozenset(),
        bottom_regions=frozenset(g.pipes),
    )


def test_abstract_observable_for_y_cubes() -> None:
    g = BlockGraph()
    g.add_pipe(
        Cube(Position3D(0, 0, 0), YCube()),
        Cube(Position3D(0, 0, 1), YCube()),
        PipeKind.from_str("XZO"),
    )
    observables, correlation_surfaces = g.get_abstract_observables()
    assert len(observables) == len(correlation_surfaces) == 1
    assert observables[0] == AbstractObservable(
        top_lines=frozenset({Cube(Position3D(0, 0, 1), YCube())}),
        bottom_regions=frozenset(),
    )


@pytest.mark.parametrize("port_type", ["x", "z"])
def test_abstract_observable_for_logical_cnot(port_type: Literal["x", "z"]) -> None:
    g = logical_cnot_block_graph(port_type)
    observables, correlation_surfaces = g.get_abstract_observables()
    assert len(observables) == len(correlation_surfaces) == 3


@pytest.mark.parametrize("port_type", ["x", "z"])
def test_abstract_observable_for_three_cnots(port_type: Literal["x", "z"]) -> None:
    g = three_cnots_block_graph(port_type)
    observables, correlation_surfaces = g.get_abstract_observables()
    assert len(observables) == len(correlation_surfaces) == 18
