from dataclasses import astuple
from typing import cast

import numpy
import numpy.typing as npt
from mpl_toolkits.mplot3d.axes3d import Axes3D

from tqec.exceptions import TQECException
from tqec.position import Position3D
from tqec.sketchup.zx_graph import NodeType, ZXGraph

CORRELATION_COLOR: dict[NodeType, str] = {
    NodeType.X: "#ff0000",
    NodeType.Z: "#0000ff",
}


def _positions_array(*positions: Position3D) -> npt.NDArray[numpy.int_]:
    return numpy.array([astuple(p) for p in positions]).T


def draw_zx_graph_on(
    graph: ZXGraph,
    ax: Axes3D,
    *,
    node_size: int = 400,
    hadamard_size: int = 200,
    edge_width: int = 1,
) -> None:
    """Draw the 3D graph using matplotlib on the provided figure.

    Args:
        ax: a 3-dimensional ax to draw on.
        node_size: The size of the node. Default is 400.
        hadamard_size: The size of the Hadamard transition. Default is 200.
        edge_width: The width of the edge. Default is 1.
    """
    non_virtual_nodes = [n for n in graph.nodes if not n.is_virtual]
    non_virtual_nodes_array = _positions_array(*[n.position for n in non_virtual_nodes])
    if non_virtual_nodes_array.size > 0:
        ax.scatter(
            *non_virtual_nodes_array,
            s=node_size,
            c=[
                "black" if n.node_type == NodeType.X else "white"
                for n in non_virtual_nodes
            ],
            alpha=1.0,
            edgecolors="black",
        )

    for edge in graph.edges:
        pos_array = _positions_array(edge.u.position, edge.v.position)
        ax.plot(
            *pos_array,
            color="tab:gray",
            linewidth=edge_width,
        )
        if edge.has_hadamard:
            hadamard_position = numpy.mean(pos_array, axis=1)
            # use yellow square to indicate Hadamard transition
            ax.scatter(
                *hadamard_position,
                s=hadamard_size,
                c="yellow",
                alpha=1.0,
                edgecolors="black",
                marker="s",
            )
    ax.grid(False)
    for dim in (ax.xaxis, ax.yaxis, ax.zaxis):
        dim.set_ticks([])
    x_limits, y_limits, z_limits = ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()  # type: ignore

    plot_radius = 0.5 * max(
        abs(limits[1] - limits[0]) for limits in [x_limits, y_limits, z_limits]
    )

    ax.set_xlim3d(
        [numpy.mean(x_limits) - plot_radius, numpy.mean(x_limits) + plot_radius]
    )
    ax.set_ylim3d(
        [numpy.mean(y_limits) - plot_radius, numpy.mean(y_limits) + plot_radius]
    )
    ax.set_zlim3d(
        [numpy.mean(z_limits) - plot_radius, numpy.mean(z_limits) + plot_radius]
    )


def draw_as_correlation_surface_on(
    graph: ZXGraph,
    ax: Axes3D,
    correlation_edge_width: int = 3,
) -> None:
    for edge in graph.edges:
        pos_array = _positions_array(edge.u.position, edge.v.position)
        if not edge.has_hadamard:
            correlation_type = edge.u.node_type
            ax.plot(
                *pos_array,
                color=CORRELATION_COLOR[correlation_type],
                linewidth=correlation_edge_width,
            )
        else:
            hadamard_position = numpy.mean(pos_array, axis=1)
            for node in [edge.u, edge.v]:
                ax.plot(
                    *numpy.hstack(
                        [
                            hadamard_position.reshape(3, 1),
                            _positions_array(node.position),
                        ]
                    ),
                    color=CORRELATION_COLOR[node.node_type],
                    linewidth=correlation_edge_width,
                )


def plot_zx_graph(
    graph: ZXGraph,
    *,
    show_correlation_subgraph_index: int | None = None,
    figsize: tuple[float, float] = (5, 6),
    title: str | None = None,
    node_size: int = 400,
    hadamard_size: int = 200,
    edge_width: int = 1,
    correlation_edge_width: int = 3,
) -> None:
    """Draw the 3D graph using matplotlib.

    Args:
        show_correlation_subgraph_index: The index of the correlation subgraph to show.
        figsize: The figure size. Default is (5, 6).
        title: The title of the plot. Default is the name of the graph.
        node_size: The size of the node. Default is 400.
        hadamard_size: The size of the Hadamard transition. Default is 200.
        edge_width: The width of the edge. Default is 1.
        correlation_edge_width: The width of the correlation edge. Default is 3.
    """
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=figsize)
    ax = cast(Axes3D, fig.add_subplot(111, projection="3d"))

    draw_zx_graph_on(
        graph,
        ax,
        node_size=node_size,
        hadamard_size=hadamard_size,
        edge_width=edge_width,
    )

    if show_correlation_subgraph_index is not None:
        correlation_subgraphs = graph.find_correlation_subgraphs()
        if show_correlation_subgraph_index >= len(correlation_subgraphs):
            raise TQECException(
                f"Only {len(correlation_subgraphs)} correlation subgraphs found."
                f"Index {show_correlation_subgraph_index} is out of range."
            )
        correlation_subgraph = correlation_subgraphs[show_correlation_subgraph_index]

        draw_as_correlation_surface_on(correlation_subgraph, ax, correlation_edge_width)

    ax.set_title(title or graph.name)
    fig.tight_layout()
    plt.show()
