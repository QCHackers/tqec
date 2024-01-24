import typing as ty

import networkx as nx
import numpy
from tqec.enums import CornerPositionEnum, TemplateRelativePositionEnum
from tqec.position import Position, Shape2D
from tqec.templates.base import JSONEncodable, Template, TemplateWithIndices


def get_corner_position(
    position: Position,
    position_corner: CornerPositionEnum,
    shape: Shape2D,
    expected_corner: CornerPositionEnum,
) -> Position:
    """Get the position of a template corner.

    This function helps in computing the position of any corner of a given
    template as long as we have the position of one of its corners.

    Examples:
    >>> get_corner_position(Position(0, 0), CornerPositionEnum.UPPER_LEFT, Shape2D(2, 2), CornerPositionEnum.UPPER_LEFT)
    Position(x=0, y=0)
    >>> get_corner_position(Position(0, 0), CornerPositionEnum.UPPER_LEFT, Shape2D(2, 2), CornerPositionEnum.LOWER_LEFT)
    Position(x=0, y=2)
    >>> get_corner_position(Position(0, 0), CornerPositionEnum.UPPER_LEFT, Shape2D(2, 2), CornerPositionEnum.UPPER_RIGHT)
    Position(x=2, y=0)
    >>> get_corner_position(Position(0, 0), CornerPositionEnum.UPPER_LEFT, Shape2D(2, 2), CornerPositionEnum.LOWER_RIGHT)
    Position(x=2, y=2)
    >>> get_corner_position(Position(0, 0), CornerPositionEnum.LOWER_RIGHT, Shape2D(2, 2), CornerPositionEnum.UPPER_LEFT)
    Position(x=-2, y=-2)


    :param position: position of the "anchor" corner.
    :param position_corner: corner which position is given as first argument.
    :param shape: 2-dimensional shape of the considerer template.
    :param expected_corner: the corner we want to compute the position of.
    :returns: the position of the expected_corner of a template of the given shape,
        knowing that the corner position_corner is at the given position.
    """
    transformation: tuple[int, int] = (
        expected_corner.value.x - position_corner.value.x,
        expected_corner.value.y - position_corner.value.y,
    )
    return Position(
        position.x + transformation[0] * shape.x,
        position.y + transformation[1] * shape.y,
    )


class TemplateOrchestrator(JSONEncodable):
    def __init__(self, templates: list[TemplateWithIndices]) -> None:
        """Manages templates positionned relatively to each other.

        This class manages a list of user-provided templates and user-provided relative
        positions to build and scale quantum error correction code.

        Template instances are stored in an ordered list. Relative positioning of these
        templates are stored in an oriented graph with:
        - vertices that are integers, representing indices of Template instances stored
          in the ordered list stored alongside the graph,
        - edges that are connecting two vertices (i.e., two Template instances) that
          are relatively positionned between each other.

        The relative position is internally stored as a tuple of corners that should
        represent the same underlying qubit. Each edge between vertices A and B should
        have a "weight" (as per networkx definition of the term) under the key
        "relative_position" that is a tuple[CornerPositionEnum, CornerPositionEnum].
        If an edge from A to B has a "relative_position" weight of (corner1, corner2),
        that means that corner1 over the template A and corner2 of the template B are
        on the same location (i.e., same physical qubit).

        The main logic in this class is located in the (private) method
        _compute_ul_absolute_position that, as its name indicate, computes the upper-left
        absolute position of each template (i.e., absolute position of the upper-left
        corner of each template).

        The coordinate system used internally by this class is:
               x-axis
          0 ------------>
          |
        y |
        | |
        a |
        x |
        i |
        s |
          |
          V

        :param templates: a list of templates forwarded to the add_templates method
            at the end of instance initialisation.
        """
        self._templates: list[Template] = []
        self._relative_position_graph = nx.DiGraph()
        self._maximum_plaquette_mapping_index: int = 0
        self.add_templates(templates)

    def add_template(
        self,
        template_to_insert: TemplateWithIndices,
    ) -> int:
        """Add the provided template to the data structure."""
        template_id: int = len(self._templates)
        indices = template_to_insert.indices
        self._templates.append(template_to_insert.template)
        self._relative_position_graph.add_node(template_id, plaquette_indices=indices)
        self._maximum_plaquette_mapping_index = max(
            self._maximum_plaquette_mapping_index, max(indices)
        )
        return template_id

    def add_templates(
        self,
        templates_to_insert: list[TemplateWithIndices],
    ) -> list[int]:
        """Add the provided templates to the data structure."""
        return [self.add_template(template) for template in templates_to_insert]

    def add_relation(
        self,
        template_id_to_position: int,
        relative_position: TemplateRelativePositionEnum,
        anchor_id: int,
    ) -> "TemplateOrchestrator":
        """Add a relative positioning between two templates.

        This method has the same effect as add_corner_relation (it internally calls it), but
        provide another interface to add a relation between two templates.

        This method is kept in the interface because the interface it provides is simpler
        to use and read than add_corner_relation.

        :param template_id_to_position: index of the template that should be positionned relatively
            to the provided anchor.
        :param relative_position: the relative position of the template provided as first parameter
            with respect to the anchor provided as third parameter. Can be any of LEFT_OF, RIGHT_OF,
            BELOW_OF and ABOVE_OF.
        :param anchor_id: index of the anchor template, i.e., the template with respect to which the
            template provided in first parameter will be positioned.
        :returns: self, to be able to chain calls to this method.
        """
        assert template_id_to_position < len(self._templates)
        assert anchor_id < len(self._templates)

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
        """Add a relative positioning between two templates.

        :param template_id_to_position_corner: a tuple containing the index of the template that
            should be positionned relatively to the provided anchor and the corner that should be
            considered.
        :param anchor_id_corner: a tuple containing the index of the (anchor) template that
            should be used to position the template instance provided in the first parameter,
            and the corner that should be considered.
        :returns: self, to be able to chain calls to this method.
        """
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
        """Computes the absolute position of each template upper-left corner.

        This is the main method of the TemplateOrchestrator class. It explores templates
        by performing a BFS on the graph of relations between templates, starting by the
        first template inserted (but any template connected to the others should work
        fine).

        The first template upper-left corner is arbitrarily positioned at the (0, 0)
        position, and each template upper-left corner is then computed from this position.
        This means in particular that this method can return positions with negative
        coordinates.

        :returns: a mapping between templates indices and their upper-left corner absolute
            position.
        """
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
            # ul_positions[src] is guaranteed to exist due to the BFS exploration order.
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
        """Get the bounding box containing all the templates from their upper-left corner position.

        :param ul_positions: a mapping between templates indices and their upper-left corner absolute
            position.
        :returns: a tuple (upper-left position, bottom-right position) representing the bounding box.
            Coordinates in each positions are not guaranteed to be positive.
        """
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
        """Get the shape of the represented code from the bounding box.

        :param ul: upper-left corner position of the bounding box.
        :param br: bottom-right corner position of the bounding box.
        """
        # ul: upper-left
        # br: bottom-right
        return Shape2D(br.x - ul.x, br.y - ul.y)

    def _get_shape_from_ul_positions(
        self, ul_positions: dict[int, Position]
    ) -> Shape2D:
        """Get the shape of the represented code from the upper-left corner positions of each template."""
        # ul: upper-left
        # br: bottom-right
        ul, br = self._get_bounding_box_from_ul_positions(ul_positions)
        return self._get_shape_from_bounding_box(ul, br)

    def build_array(self, indices_map: tuple[int, ...]) -> numpy.ndarray:
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
            plaquette_indices: list[int] = [
                indices_map[i]
                for i in self._relative_position_graph.nodes[tid]["plaquette_indices"]
            ]
            # Subtracting bbul (upper-left bounding box position) from each coordinate to stick
            # the represented code to the axes and avoid having negative indices.
            x = tul.x - bbul.x
            y = tul.y - bbul.y
            # Numpy indexing is (y, x) in our coordinate system convention.
            ret[y : y + tshapey, x : x + tshapex] = template.instanciate(
                *plaquette_indices
            )
        return ret

    def instanciate(self, *plaquette_indices: int) -> numpy.ndarray:
        return self.build_array(plaquette_indices)

    def scale_to(self, k: int) -> "TemplateOrchestrator":
        """Scales all the scalable component templates to the given scale k.

        The scale k of a **scalable template** is defined to be **half** the dimension/size
        of the **scalable axis** of the template. For example, a scalable 4x4 square T has a
        scale of 2 for both its axis. This means the dimension/size of the scaled axis is
        enforced to be even, which avoids some invalid configuration of the template.

        Note that this function scales to INLINE, so the instance on which it is called is
        modified in-place AND returned.

        :param k: the new scale of the component templates.
        :returns: self, once scaled.
        """
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

    @property
    def expected_plaquettes_number(self) -> int:
        return self._maximum_plaquette_mapping_index + 1
