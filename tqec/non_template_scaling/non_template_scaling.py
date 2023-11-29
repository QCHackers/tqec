import time
import matplotlib.pyplot as plt

from tqec.non_template_scaling.display_data import generate_coordinates, plot_quiver


#A class for edges
class Edge:

    def __init__(self):
        self.length = None
        self.turning = None
        self.next_edge = None

    def set_length(self, length):
        self.length = length

    def set_turning(self, turning):
        self.turning = turning

    def set_next_edge(self, next_edge):
        self.next_edge = next_edge

#A class for whole patches of surface code
class Patch:

    def __init__(self, edge_data):

        self.edges = []

        self.init_edges(edge_data)

        self.num_edges = len(self.edges)

    def init_edges(self, edge_data):

        for i in range(len(edge_data)):
            E = Edge()
            E.set_length(edge_data[i][0])
            E.set_turning(edge_data[i][1])
            self.edges += [E]

        for i in range(len(self.edges)):
            self.edges[i].set_next_edge(self.edges[(i + 1) % len(self.edges)])

    def scale_up(self):
        d_lengths = [0 for i in range(self.num_edges)]

        while min(d_lengths) < 1:
            for i in range(self.num_edges):
                if d_lengths[i] < 1:
                    S = self.shift(self.edges[i], 1 - d_lengths[i])
                    d_lengths[i] = 1
                    d_lengths[(i + 2) % self.num_edges] += S

    def shift(self, edge, k):
        edge.length += k
        sign = edge.turning * edge.next_edge.turning
        edge.next_edge.next_edge.length += sign * k
        return sign * k

    def generate_edge_data(self):
        edge_data = [[edge.length, edge.turning] for edge in self.edges]

        return edge_data

    def make_plot(self):

        initial_edge_data = self.generate_edge_data()
        initial_edge_coords=generate_coordinates(initial_edge_data)
        x_pos, y_pos, x_dir, y_dir = initial_edge_coords

        plot_quiver(x_pos, y_pos, x_dir, y_dir, initial_edge_coords, label='Data', pause_time=0.2)

    def animate_scaling(self):

        initial_edge_data = self.generate_edge_data()
        initial_edge_coords = generate_coordinates(initial_edge_data)

        d_lengths = [0 for _ in range(self.num_edges)]

        while min(d_lengths) < 1:
            for j in range(self.num_edges):
                if d_lengths[j] < 1:
                    S = self.shift(self.edges[j], 1 - d_lengths[j])
                    d_lengths[j] = 1
                    d_lengths[(j + 2) % self.num_edges] += S

                edge_data = self.generate_edge_data()
                x_pos, y_pos, x_dir, y_dir = generate_coordinates(edge_data)

                plot_quiver(x_pos, y_pos, x_dir, y_dir, initial_edge_coords, label='Data', pause_time=0.2)

#Here are a bunch of examples of the code in action

# test_edge_data = [[3, +1], [3, -1], [2, -1], [3, +1], [3, +1], [3, -1],
#                     [2, -1], [3, +1], [3, +1], [8, +1], [13, +1], [8, +1]]
# P = Patch(test_edge_data)
# P.animate_scaling()
# #P.make_plot()
# plt.show()

"""test_edge_data = [[8,+1],[4,+1],[2,+1],[1,+1],[1,-1],[2,-1],[2,-1],[2,-1],[1,+1],[1,+1],[4,+1],[1,+1],[1,-1],[2,-1],[2,-1],[2,-1],[1,+1],[1,+1],[2,+1],[4,+1]]
P = Patch(test_edge_data)
P.animate_scaling()
#P.make_plot()
plt.show()"""

"""test_edge_data = [[4, +1], [10, +1], [8, +1], [4, -1], [4, +1], [8, +1],[5,-1],[2,+1],[3,+1],[4,-1]]
P = Patch(test_edge_data)
P.animate_scaling()
#P.make_plot()
plt.show()"""


"""test_edge_data = [[4, +1], [6, -1], [6, +1], [4, +1], [10, +1], [10, +1]]
P = Patch(test_edge_data)
P.animate_scaling()
P.make_plot()
plt.show()"""


"""test_edge_data_shifted = [[3, +1], [3, +1], [8, +1], [13, +1], [8, +1], [3, +1], [3, -1], [2, -1],
                [3, +1], [3, +1], [3, -1], [2, -1]]
P = Patch(test_edge_data_shifted)
#P.animate_scaling()
P.make_plot()
plt.show()"""


"""test_edge_data_2 = [[4, 1], [4, 1], [4, 1], [4, 1]]
P2 = Patch(test_edge_data_2)
P2.animate_scaling()
plt.show()"""

"""
test_edge_data_3 = [[1, +1], [7, -1], [1, -1], [6, +1], [2, +1], [3, -1], [2, -1], [2, +1], [1, +1], [2, -1],
                        [1, +1], [3, -1], [1, -1], [8, +1], [2, +1], [2, -1], [6, +1], [7, +1], [5, +1], [5, +1],
                        [3, +1], [3, +1], [1, +1], [2, -1], [1, -1], [3, -1], [3, -1], [5, -1], [5, -1], [2, +1],
                        [1, -1], [4, +1], [4, +1], [3, -1], [3, -1], [3, +1], [3, +1], [2, -1], [1, +1], [1, +1],
                        [1, -1], [5, +1]]  # very messed up with a spiral in it.
P3 = Patch(test_edge_data_3)
P3.animate_scaling()
plt.show()"""

"""test_edge_data_4 = [[1, +1], [7, -1], [1, -1], [6, +1], [2, +1], [3, -1], [2, -1], [2, +1], [1, +1], [2, -1],
                        [1, +1], [3, -1], [1, -1], [8, +1], [2, +1], [5, +1], [1, -1], [4, +1], [4, +1], [3, -1],
                        [3, -1], [3, +1], [3, +1], [2, -1], [1, +1], [1, +1], [1, -1], [5, +1]]

# # same as 3 but without the spiral
P3 = Patch(test_edge_data_4)
P3.animate_scaling()
plt.show()"""




