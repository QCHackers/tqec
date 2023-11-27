import typing as ty

from tqec.errors import TemplateNotInOrchestrator
from tqec.templates.base import Template, TemplateWithPlaquettes
from tqec.enums import (
    CornerPositionEnum,
    TemplateRelativePositionEnum,
    opposite_relative_position,
    ABOVE_OF,
    BELOW_OF,
    LEFT_OF,
    RIGHT_OF,
)

import networkx as nx
import numpy

type RelativePosition = TemplateRelativePositionEnum | tuple[
    CornerPositionEnum, CornerPositionEnum
]


def get_corner_position(
    position: tuple[int, int],
    position_corner: CornerPositionEnum,
    shape: tuple[int, int],
    expected_corner: CornerPositionEnum,
) -> tuple[int, int]:
    transformation: tuple[int, int] = (
        expected_corner.value[0] - position_corner.value[0],
        expected_corner.value[1] - position_corner.value[1],
    )
    return (
        position[0] + transformation[0] * shape[0],
        position[1] + transformation[1] * shape[1],
    )


class TemplateOrchestrator(Template):
    def __init__(self, templates: list[TemplateWithPlaquettes]) -> None:
        self._templates: list[Template] = []
        self._relative_position_graph = nx.DiGraph()
        self.add_templates(templates)

    def add_template(
        self,
        template_to_insert: TemplateWithPlaquettes,
    ) -> int:
        # Add the new template to the data structure
        template_id: int = len(self._templates)
        self._templates.append(template_to_insert.template)
        self._relative_position_graph.add_node(
            template_id, plaquette_indices=template_to_insert.plaquettes
        )
        return template_id

    def add_templates(
        self,
        templates_to_insert: list[TemplateWithPlaquettes],
    ) -> list[int]:
        return [self.add_template(template) for template in templates_to_insert]

    def add_relation(
        self,
        template_id_to_position: int,
        relative_position: TemplateRelativePositionEnum,
        anchor_id: int,
    ) -> "TemplateOrchestrator":
        assert template_id_to_position < len(self._templates)
        assert anchor_id < len(self._templates)
        assert isinstance(relative_position, TemplateRelativePositionEnum)
        # Add 2 symmetric edges on the graph to encode the relative positioning information
        # provided by the user by calling this methods.
        self._relative_position_graph.add_edge(
            anchor_id,
            template_id_to_position,
            relative_position=relative_position,
        )
        self._relative_position_graph.add_edge(
            template_id_to_position,
            anchor_id,
            relative_position=opposite_relative_position(relative_position),
        )
        return self

    def add_corner_relation(
        self,
        template_id_to_position_corner: tuple[int, CornerPositionEnum],
        anchor_id_corner: tuple[int, CornerPositionEnum],
    ) -> "TemplateOrchestrator":
        anchor_id, anchor_corner = anchor_id_corner
        template_id, template_corner = template_id_to_position_corner
        assert template_id < len(self._templates)
        assert anchor_id < len(self._templates)
        # Add 2 symmetric edges on the graph to encode the relative positioning information
        # provided by the user by calling this methods.
        self._relative_position_graph.add_edge(
            anchor_id,
            template_id,
            relative_position=(anchor_corner, template_corner),
        )
        self._relative_position_graph.add_edge(
            template_id,
            anchor_id,
            relative_position=(template_corner, anchor_corner),
        )
        return self

    def _find_template_id(self, template: Template) -> int:
        try:
            return self._templates.index(template)
        except ValueError:
            raise TemplateNotInOrchestrator(self, template)

    def _compute_ul_absolute_position(self) -> dict[int, tuple[int, int]]:
        ul_positions: dict[int, tuple[int, int]] = {0: (0, 0)}
        src: int
        dest: int
        # Compute the upper-left (ul) position of all the templates
        for src, dest in nx.bfs_edges(self._relative_position_graph, 0):
            relative_position: RelativePosition | None = (
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
            if isinstance(relative_position, TemplateRelativePositionEnum):
                if relative_position == ABOVE_OF:
                    ul_positions[dest] = (
                        src_position[0] - dest_shape[0],
                        src_position[1],
                    )
                elif relative_position == BELOW_OF:
                    ul_positions[dest] = (
                        src_position[0] + src_shape[0],
                        src_position[1],
                    )
                elif relative_position == LEFT_OF:
                    ul_positions[dest] = (
                        src_position[0],
                        src_position[1] - dest_shape[1],
                    )
                else:  # relative_position == RIGHT_OF:
                    ul_positions[dest] = (
                        src_position[0],
                        src_position[1] + src_shape[1],
                    )
            else:  # isinstance(relative_position, tuple[CornerPositionEnum, CornerPositionEnum])
                src_corner: CornerPositionEnum
                dest_corner: CornerPositionEnum
                src_corner, dest_corner = relative_position
                # Compute the anchor corner
                anchor_position: tuple[int, int] = get_corner_position(
                    src_position, CornerPositionEnum.UPPER_LEFT, src_shape, src_corner
                )
                # Compute the upper-left position of the destination
                ul_positions[dest] = get_corner_position(
                    anchor_position,
                    dest_corner,
                    dest_shape,
                    CornerPositionEnum.UPPER_LEFT,
                )

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

    def to_dict(self) -> dict[str, ty.Any]:
        return {
            "templates": [t.to_dict() for t in self._templates],
            "connections": [
                {"source_idx": source, "target_idx": target, "direction": direction}
                for source, target, direction in self._relative_position_graph.edges.data(
                    "relative_position"  # type: ignore
                )
            ],
        }
