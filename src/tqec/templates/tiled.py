from copy import deepcopy
from typing import Sequence

import numpy
import numpy.typing as npt
from typing_extensions import override

from tqec.exceptions import TQECException
from tqec.position import Displacement, Position2D, Shape2D
from tqec.templates.base import RectangularTemplate
from tqec.templates.enums import TemplateSide
from tqec.templates.scale import Scalable2D


class TiledTemplate(RectangularTemplate):
    def __init__(
        self,
        template_by_position: dict[Position2D, RectangularTemplate],
        k: int = 2,
        default_increments: Displacement | None = None,
    ) -> None:
        """A template representing a tiling of other templates.

        The tiles are indexed by their position in the tiling.
        """
        super().__init__(k, default_increments)
        if not template_by_position:
            raise TQECException(
                "Cannot create a tiled template with an empty template map."
            )

        scalable_shapes = {
            template.scalable_shape for template in template_by_position.values()
        }
        if len(scalable_shapes) != 1:
            raise TQECException(
                "All templates in the TiledTemplate should have the same scalable shape."
            )
        self._base_scalable_shape = scalable_shapes.pop()

        all_positions = list(template_by_position.keys())
        min_x = min(position.x for position in all_positions)
        max_x = max(position.x for position in all_positions)
        min_y = min(position.y for position in all_positions)
        max_y = max(position.y for position in all_positions)
        # Shift the bounding box to the origin
        self._origin_shift = Displacement(min_x, min_y)
        self._nx = max_x - min_x + 1
        self._ny = max_y - min_y + 1

        self._template_by_position = deepcopy(template_by_position)
        self.scale_to(k)

    def get_indices_map_for_instantiation(
        self,
        instantiate_indices: Sequence[int] | None = None,
    ) -> dict[Position2D, dict[int, int]]:
        if instantiate_indices is None:
            instantiate_indices = list(range(1, self.expected_plaquettes_number + 1))
        index_count = 0
        indices_map = {}
        for position, template in self._template_by_position.items():
            indices_map[position] = {
                i: instantiate_indices[i - 1 + index_count]
                for i in range(1, template.expected_plaquettes_number + 1)
            }
            index_count += template.expected_plaquettes_number
        return indices_map

    @property
    def origin_shift(self) -> Displacement:
        return self._origin_shift

    @override
    def scale_to(self, k: int) -> None:
        self._k = k
        for template in self._template_by_position.values():
            template.scale_to(k)

    @property
    @override
    def scalable_shape(self) -> Scalable2D:
        """Returns a scalable version of the template shape."""
        return Scalable2D(
            self._nx * self._base_scalable_shape.x,
            self._ny * self._base_scalable_shape.y,
        )

    @property
    def tile_shape(self) -> Shape2D:
        return self._base_scalable_shape.to_shape_2d(self._k)

    @property
    @override
    def expected_plaquettes_number(self) -> int:
        """Returns the number of plaquettes expected from the `instantiate`
        method.

        Returns:
            the number of plaquettes expected from the `instantiate` method.
        """
        return sum(
            template.expected_plaquettes_number
            for template in self._template_by_position.values()
        )

    @override
    def get_plaquette_indices_on_sides(self, _: list[TemplateSide]) -> list[int]:
        """Get the indices of plaquettes that are located on the provided
        sides.

        Args:
            sides: the sides to recover plaquettes from.

        Returns:
            a non-ordered list of plaquette numbers.
        """
        raise NotImplementedError()

    @override
    def instantiate(
        self, plaquette_indices: Sequence[int] | None = None
    ) -> npt.NDArray[numpy.int_]:
        """Generate the numpy array representing the template.

        Args:
            plaquette_indices: the plaquette indices that will be forwarded to
                the underlying Template instance's instantiate method. Defaults
                to `range(1, self.expected_plaquettes_number + 1)` if `None`.

        Returns:
            a numpy array with the given plaquette indices arranged according to
            the underlying shape of the template.
        """
        indices_map = self.get_indices_map_for_instantiation(plaquette_indices)

        tile_shape = self._base_scalable_shape.to_numpy_shape(self.k)
        ret = numpy.zeros(self.shape.to_numpy_shape(), dtype=numpy.int_)
        for pos, template in self._template_by_position.items():
            imap = indices_map[pos]
            indices = [
                imap[i] for i in range(1, template.expected_plaquettes_number + 1)
            ]
            sub_template = template.instantiate(indices)
            shifted_pos = Position2D(
                pos.x - self.origin_shift.x, pos.y - self.origin_shift.y
            )
            ret[
                shifted_pos.y * tile_shape[0] : (shifted_pos.y + 1) * tile_shape[0],
                shifted_pos.x * tile_shape[1] : (shifted_pos.x + 1) * tile_shape[1],
            ] = sub_template
        return ret
