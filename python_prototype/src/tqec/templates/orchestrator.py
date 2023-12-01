import typing as ty

from tqec.errors import TemplateNotInOrchestrator
from tqec.templates.base import JSONEncodable, Template, TemplateWithPlaquettes
from tqec.enums import (
    CornerPositionEnum,
    TemplateRelativePositionEnum,
)
from tqec.position import Position, Shape2D

import networkx as nx
import numpy


def get_corner_position(
    position: Position,
    position_corner: CornerPositionEnum,
    shape: Shape2D,
    expected_corner: CornerPositionEnum,
) -> Position:
    transformation: tuple[int, int] = (
        expected_corner.value.x - position_corner.value.x,
        expected_corner.value.y - position_corner.value.y,
    )
    return Position(
        position.x + transformation[0] * shape.x,
        position.y + transformation[1] * shape.y,
    )


class TemplateOrchestrator(JSONEncodable):
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

        anchor_corner: CornerPositionEnum
        template_corner: CornerPositionEnum
        if relative_position == TemplateRelativePositionEnum.ABOVE_OF:
            anchor_corner, template_corner = (
                CornerPositionEnum.UPPER_LEFT,
                CornerPositionEnum.LOWER_LEFT,
            )
        elif relative_position == TemplateRelativePositionEnum.BELOW_OF:
            anchor_corner, template_corner = (
                CornerPositionEnum.LOWER_LEFT,
                CornerPositionEnum.UPPER_LEFT,
            )
        elif relative_position == TemplateRelativePositionEnum.RIGHT_OF:
            anchor_corner, template_corner = (
                CornerPositionEnum.UPPER_RIGHT,
                CornerPositionEnum.UPPER_LEFT,
            )
        else:  # relative_position == TemplateRelativePositionEnum.LEFT_OF:
            anchor_corner, template_corner = (
                CornerPositionEnum.UPPER_LEFT,
                CornerPositionEnum.UPPER_RIGHT,
            )
        return self.add_corner_relation(
            (template_id_to_position, template_corner), (anchor_id, anchor_corner)
        )

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

    def _compute_ul_absolute_position(self) -> dict[int, Position]:
        ul_positions: dict[int, Position] = {0: Position(0, 0)}
        src: int
        dest: int
        # Compute the upper-left (ul) position of all the templates
        for src, dest in nx.bfs_edges(self._relative_position_graph, 0):
            relative_position: tuple[
                CornerPositionEnum, CornerPositionEnum
            ] | None = self._relative_position_graph.get_edge_data(src, dest).get(
                "relative_position"
            )
            assert (
                relative_position is not None
            ), f"Found an edge from {src} to {dest} that does not have a relative position."
            # Getting the positions and shape that will be needed to compute the ul_position
            # for dest.
            src_ul_position = ul_positions[src]
            src_shape = self._templates[src].shape
            dest_shape = self._templates[dest].shape

            src_corner: CornerPositionEnum
            dest_corner: CornerPositionEnum
            src_corner, dest_corner = relative_position
            # Compute the anchor corner
            anchor_position: Position = get_corner_position(
                src_ul_position,
                CornerPositionEnum.UPPER_LEFT,
                src_shape,
                src_corner,
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
        self, ul_positions: dict[int, Position]
    ) -> tuple[Position, Position]:
        # ul: upper-left
        # br: bottom-right
        ul, br = Position(0, 0), Position(0, 0)
        # tid: template id
        # tulx: template upper-left
        for tid, tul in ul_positions.items():
            # tshape: template shape
            tshape = self._templates[tid].shape
            ul = Position(min(ul.x, tul.x), min(ul.y, tul.y))
            br = Position(max(br.x, tul.x + tshape.x), max(br.y, tul.y + tshape.y))
        return ul, br

    def _get_shape_from_bounding_box(self, ul: Position, br: Position) -> Shape2D:
        # ul: upper-left
        # br: bottom-right
        return Shape2D(br.x - ul.x, br.y - ul.y)

    def _get_shape_from_ul_positions(
        self, ul_positions: dict[int, Position]
    ) -> Shape2D:
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

        ret = numpy.zeros(shape.to_numpy_shape(), dtype=int)
        # tid: template id
        # tul: template upper-left
        for tid, tul in ul_positions.items():
            template = self._templates[tid]
            # tshapex: template shape x coordinate
            # tshapey: template shape y coordinate
            tshapey, tshapex = template.shape.to_numpy_shape()
            plaquette_indices: list[int] = self._relative_position_graph.nodes[tid][
                "plaquette_indices"
            ]
            x = tul.x - bbul.x
            y = tul.y - bbul.y
            # Numpy indexing is (y, x) in our coordinate system convention.
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
        return self._get_shape_from_ul_positions(
            self._compute_ul_absolute_position()
        ).to_numpy_shape()

    def to_dict(self) -> dict[str, ty.Any]:
        return {
            # __class__ is "TemplateOrchestrator" here, whatever the type of self is. This is different
            # from what is done in the Template base class. This is done to avoid users subclassing this
            # class and having a subclass name we do not control in the "type" entry.
            "type": __class__.__name__,
            "kwargs": {
                "templates": [t.to_dict() for t in self._templates],
            },
            "connections": [
                {
                    "source_idx": source,
                    "target_idx": target,
                    "source_corner": source_corner,
                    "target_corner": target_corner,
                }
                for source, target, (
                    source_corner,
                    target_corner,
                ) in self._relative_position_graph.edges.data(
                    "relative_position"  # type: ignore
                )
            ],
        }
