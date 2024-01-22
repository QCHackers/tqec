from time import sleep

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
