"""Defines some helper functions to plot into insets"""

# required for "3d" projection even though not explicitly used
from matplotlib.axes import Axes
from mpl_toolkits.mplot3d.axes3d import Axes3D

from tqec.sketchup.zx_graph import ZXGraph


def add_inset_axes3d(
    ax_target: Axes, bounds: tuple[float, float, float, float]
) -> Axes3D:
    """Wrapper around `fig.add_axes` to achieve `ax.inset_axes` functionality
    that works also for insetting 3D plot on 2D ax/figures
    """
    ax = ax_target.inset_axes(bounds, projection="3d")
    assert isinstance(ax, Axes3D)
    return ax


def plot_observable_as_inset(
    ax_target: Axes,
    zx_graph: ZXGraph,
    correlation_surface: ZXGraph,
    bounds: tuple[float, float, float, float] = (0.5, 0.0, 0.5, 0.5),
) -> None:
    """Plot the provided observable as an inset in the provided ax.

    Args:
        ax_target: the ax to insert an inset in to plot the correlation surface.
        bounds: (x0, y0, width, height) where (x0, y0) is the position of the
            lower-left corner of the inset. All coordinates are normalized to
            [0, 1] meaning that an input of (0, 0, 1, 1) will span the whole
            `ax_target`.
        zx_graph: ZX graph used.
        correlation_surface: correlation surface over the provided `zx_graph` to
            draw.
    """
    inset_ax = add_inset_axes3d(ax_target, bounds)
    zx_graph.draw_as_zx_graph_on(inset_ax, node_size=50)
    correlation_surface.draw_as_correlation_surface_on(inset_ax)
    inset_ax.set_facecolor((0.0, 0.0, 0.0, 0.0))
