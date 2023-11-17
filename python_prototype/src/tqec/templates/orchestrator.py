from tqec.templates.base import Template, TemplateWithPlaquettes
from tqec.enums import (
    TemplateRelativePositionEnum,
    opposite_relative_position,
    ABOVE_OF,
    BELOW_OF,
    LEFT_OF,
    RIGHT_OF,
)

import networkx as nx
import numpy


class TemplateOrchestrator(Template):
    def __init__(self, first_template: TemplateWithPlaquettes) -> None:
        self._templates: list[Template] = [first_template.template]
        self._relative_position_graph = nx.DiGraph()
        self._relative_position_graph.add_node(
            0, plaquette_indices=first_template.plaquettes
        )

    def add_template(
        self,
        template_to_insert: TemplateWithPlaquettes,
        relative_position: TemplateRelativePositionEnum,
        anchor: Template | TemplateWithPlaquettes,
    ) -> "TemplateOrchestrator":
        # Recovering the Template instance, we do not care about the plaquettes of the anchor.
        if isinstance(anchor, TemplateWithPlaquettes):
            anchor = anchor.template
        # IDs of the template and anchor in the internal graph
        template_id = len(self._templates)
        anchor_id = self._templates.index(anchor)
        # Add the new template to the data structure
        self._templates.append(template_to_insert.template)
        self._relative_position_graph.add_node(
            template_id, plaquette_indices=template_to_insert.plaquettes
        )
        # Add 2 symmetric edges on the graph to encode the relative positioning information
        # provided by the user by calling this methods.
        self._relative_position_graph.add_edge(
            anchor_id, template_id, relative_position=relative_position
        )
        self._relative_position_graph.add_edge(
            template_id,
            anchor_id,
            relative_position=opposite_relative_position(relative_position),
        )
        return self

    def and_also(
        self,
        relative_position: TemplateRelativePositionEnum,
        anchor: Template | TemplateWithPlaquettes,
    ) -> "TemplateOrchestrator":
        # Recovering the Template instance, we do not care about the plaquettes of the anchor.
        if isinstance(anchor, TemplateWithPlaquettes):
            anchor = anchor.template
        # IDs of the template and anchor in the internal graph
        # Minus 1 here as the template has already been inserted.
        template_id = len(self._templates) - 1
        anchor_id = self._templates.index(anchor)
        # Add 2 symmetric edges on the graph to encode the relative positioning information
        # provided by the user by calling this methods.
        self._relative_position_graph.add_edge(
            anchor_id, template_id, relative_position=relative_position
        )
        self._relative_position_graph.add_edge(
            template_id,
            anchor_id,
            relative_position=opposite_relative_position(relative_position),
        )
        return self

    def _compute_ul_absolute_position(self) -> dict[int, tuple[int, int]]:
        ul_positions: dict[int, tuple[int, int]] = {0: (0, 0)}
        src: int
        dest: int
        # Compute the upper-left (ul) position of all the templates
        for src, dest in nx.bfs_edges(self._relative_position_graph, 0):
            relative_position: TemplateRelativePositionEnum | None = (
                self._relative_position_graph.get_edge_data(src, dest).get(
                    "relative_position"
                )
            )
            assert (
                relative_position is not None
            ), f"Found an edge from {src} to {dest} that does not have a relative position."
            # Getting the positions and shape that will be needed to compute the ul_position
            # for dest.
            src_position = ul_positions[src]
            src_shape = self._templates[src].shape
            dest_shape = self._templates[dest].shape
            # The convention for tuples is that they encode coordinates in (y, x).
            # This is to adhere to numpy array indexing for regular 2-dimensional arrays
            # that are indexed as arr[y, x].
            if relative_position == ABOVE_OF:
                ul_positions[dest] = (src_position[0] - dest_shape[0], src_position[1])
            elif relative_position == BELOW_OF:
                ul_positions[dest] = (src_position[0] + src_shape[0], src_position[1])
            elif relative_position == LEFT_OF:
                ul_positions[dest] = (src_position[0], src_position[1] - dest_shape[1])
            else:  # relative_position == RIGHT_OF:
                ul_positions[dest] = (src_position[0], src_position[1] + src_shape[1])
        return ul_positions

    def _get_bounding_box_from_ul_positions(
        self, ul_positions: dict[int, tuple[int, int]]
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        # ul: upper-left
        # br: bottom-right
        ul, br = (0, 0), (0, 0)
        # Tuple convention is (y, x)
        # tid: template id
        # ulx: upper-left x coordinate
        # uly: upper-left y coordinate
        for tid, (uly, ulx) in ul_positions.items():
            # tshape: template shape
            tshape = self._templates[tid].shape
            ul = (min(ul[0], uly), min(ul[1], ulx))
            br = (max(br[0], uly + tshape[0]), max(br[1], ulx + tshape[1]))
        return ul, br

    def _get_shape_from_bounding_box(
        self, ul: tuple[int, int], br: tuple[int, int]
    ) -> tuple[int, int]:
        # ul: upper-left
        # br: bottom-right
        # Tuple convention is (y, x)
        return (br[0] - ul[0], br[1] - ul[1])

    def _get_shape_from_ul_positions(
        self, ul_positions: dict[int, tuple[int, int]]
    ) -> tuple[int, int]:
        # ul: upper-left
        # br: bottom-right
        ul, br = self._get_bounding_box_from_ul_positions(ul_positions)
        return self._get_shape_from_bounding_box(ul, br)

    def build_array(self) -> numpy.ndarray:
        # ul: upper-left
        ul_positions = self._compute_ul_absolute_position()
        # bbul: bounding-box upper-left
        # bbbr: bounding-box bottom-right
        bbul, bbbr = self._get_bounding_box_from_ul_positions(ul_positions)
        shape = self._get_shape_from_bounding_box(bbul, bbbr)

        ret = numpy.zeros(shape, dtype=int)
        # Tuple convention is (y, x)
        # tid: template id
        # ulx: upper-left x coordinate
        # uly: upper-left y coordinate
        for tid, (uly, ulx) in ul_positions.items():
            template = self._templates[tid]
            # tshapex: template shape x coordinate
            # tshapey: template shape y coordinate
            tshapey, tshapex = template.shape
            plaquette_indices: list[int] = self._relative_position_graph.nodes[tid][
                "plaquette_indices"
            ]
            # Tuple convention is (y, x)
            y = uly - bbul[0]
            x = ulx - bbul[1]
            ret[y : y + tshapey, x : x + tshapex] = template.instanciate(
                *plaquette_indices
            )
        return ret

    def instanciate(self, *plaquette_indices: int) -> numpy.ndarray:
        assert (
            len(plaquette_indices) == 0
        ), "Orchestrator instances should not need any plaquette indices to call instantiate."
        return self.build_array()

    def scale_to(self, k: int) -> "TemplateOrchestrator":
        for t in self._templates:
            t.scale_to(k)
        return self

    @property
    def shape(self) -> tuple[int, int]:
        return self._get_shape_from_ul_positions(self._compute_ul_absolute_position())
