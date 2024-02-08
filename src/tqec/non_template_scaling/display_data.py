import matplotlib.pyplot as plt
import numpy as np


def plot_quiver(x_pos, y_pos, x_dir, y_dir, initial_data_plot, label, pause_time=0.5):
    plt.clf()
    plt.quiver(x_pos, y_pos, x_dir, y_dir, scale=40, label=label)
    plt.title("Patch Scaling")
    plt.legend()
    plt.axis([-5, 35, -20, 20])
    plt.gca().set_aspect("equal", adjustable="box")
    plt.pause(pause_time)


def generate_coordinates(data):
    """data: input as a list [(#, +-1), (#, +-1), ... (#, +-1)]
    where each number is the length and the sign is the turning.
    this function constructs the coordinates for the positions
    and directions of each of these arrows. This prepares the
    data to be drawn with matplotlib.
    """

    x_pos = []
    y_pos = []
    x_dir = []
    y_dir = []

    current_x_pos = 0  # x,y coords, arbitrarily chosen to start at (0,0)
    current_y_pos = 0
    current_x_dir = (
        1  # direction on the grid, arbitrarily chosen to start at (1,0). can be (+-1,0), (0, +-1).
    )
    current_y_dir = 0

    for (length, turning) in data:
        # graph where we are
        x_pos.append(current_x_pos)
        y_pos.append(current_y_pos)

        # graph the direction we are going in
        x_dir.append(length * current_x_dir)
        y_dir.append(length * current_y_dir)

        # move along this edge and update position
        current_x_pos += length * current_x_dir
        current_y_pos += length * current_y_dir

        # change direction according to this edge's turning and update direction.
        # (x, y), t ----> (t * y, -t * x). I computed this rule for updating direction
        # on a chalkboard.
        save_current_x_dir = current_x_dir
        current_x_dir = turning * current_y_dir
        current_y_dir = -turning * save_current_x_dir

    return x_pos, y_pos, x_dir, y_dir


def display_shape(x_pos, y_pos, x_dir, y_dir):
    # Creating plot
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.quiver(x_pos, y_pos, x_dir, y_dir, scale=16)

    ax.axis([-8, 8, -8, 8])
    ax.set_aspect("equal")

    # show plot
    plt.show()
