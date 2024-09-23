from __future__ import annotations

from dataclasses import dataclass

import numpy
import numpy.typing as npt

from tqec.exceptions import TQECException


@dataclass(frozen=True)
class UniqueSubTemplates:
    """Stores information on the sub-templates of a specific radius present on
    a larger `Template` instance.

    A sub-template is defined here as a portion of a `Template` instantiation.
    In other words, a sub-template is a sub-array of the array resulting from
    calling the method `Template.instantiate` on any `Template` instance.
    The size of this sub-array is defined by its `radius`, which is computed
    according to the Manhattan distance.

    For example, let's say you have the following array from calling
    `Template.instantiate` on a `Template` instance:

    ```
    1  5  6  5  6  2
    7  9 10  9 10 11
    8 10  9 10  9 12
    7  9 10  9 10 11
    8 10  9 10  9 12
    3 13 14 13 14  4
    ```

    Focusing on the top-left `9` (coordinates `(1, 1)` in the array), the
    following sub-array is a sub-template of radius `1`, centered on the
    `(1, 1)` coordinate of the above instantiation:

    ```
    1  5  6
    7  9 10
    8 10  9
    ```

    Still focusing on the top-left `9`, the following sub-array is a
    sub-template of radius `2`, centered on the `(1, 1)` coordinate of the
    above instantiation:

    ```
    .  .  .  .  .
    .  1  5  6  5
    .  7  9 10  9
    .  8 10  9 10
    .  7  9 10  9
    ```

    Note the inclusion of `.` that are here to represent `0` (i.e., the
    absence of plaquette at that particular point) because there is no
    plaquette in the original `Template` instantiation.

    This dataclass efficiently stores all the sub-templates of a given
    `Template` instantiation and of a given `radius`.


    Attributes:
        subtemplate_indices: an array that has the same shape as the
            original `Template` instantiation but stores sub-template
            indices referencing sub-templates from the `subtemplates`
            attribute. The integers in this array do NOT represent
            plaquette indices.
        subtemplates: a store of sub-template (values) indexed by integers
            (keys) that link the sub-template center to the original
            template instantiation thanks to `subtemplate_indices`.

    Raises:
        TQECException: if any index in `self.subtemplate_indices` is
            not present in `self.subtemplates.keys()`.
        TQECException: if any of the sub-template shapes is non-square
            or of even width or length.
        TQECException: if not all the sub-template shapes in
            `self.subtemplates.values()` are equal.
    """

    subtemplate_indices: npt.NDArray[numpy.int_]
    subtemplates: dict[int, npt.NDArray[numpy.int_]]

    def __post_init__(self) -> None:
        # We do not need a valid subtemplate for the 0 index.
        indices = frozenset(numpy.unique(self.subtemplate_indices)) - {0}
        if not indices.issubset(self.subtemplates.keys()):
            raise TQECException(
                "Found an index in subtemplate_indices that does "
                "not correspond to a valid subtemplate."
            )
        shape = next(iter(self.subtemplates.values())).shape
        if shape[0] != shape[1]:
            raise TQECException(
                "Subtemplate shapes are expected to be square. "
                f"Found the shape {shape} that is not a square."
            )
        if shape[0] % 2 == 0:
            raise TQECException(
                "Subtemplate shapes are expected to be squares with an "
                f"odd size length. Found size length {shape[0]}."
            )
        if not all(
            subtemplate.shape == shape for subtemplate in self.subtemplates.values()
        ):
            raise TQECException(
                "All the subtemplates should have the exact same shape. "
                "Found one with a differing shape."
            )

    @property
    def manhattan_radius(self) -> int:
        return next(iter(self.subtemplates.values())).shape[0] // 2


def get_spatially_distinct_subtemplates(
    instantiation: npt.NDArray[numpy.int_],
    manhattan_radius: int = 1,
    avoid_zero_plaquettes: bool = True,
) -> UniqueSubTemplates:
    """Returns a representation of all the distinct sub-templates of the
    provided manhattan radius.

    Note:
        This method will likely be inefficient for large templates (i.e., large
        values of `k`) or for large Manhattan radiuses, both in terms of memory
        used and computation time.
        Subclasses are invited to reimplement that method using a specialized
        algorithm (or hard-coded values) to speed things up.

    Args:
        instantiation: a 2-dimensional array representing the instantiated
            template on which sub-templates should be computed.
        manhattan_radius: radius of the considered ball using the Manhattan
            distance. Only squares with sides of `2*manhattan_radius+1`
            plaquettes will be considered.
        avoid_zero_plaquettes: `True` if sub-templates with an empty plaquette
            (i.e., 0 value in the instantiation of the Template instance) at
            its center should be ignored. Default to `True`.

    Returns:
        a representation of all the sub-templates found.
    """
    y, x = instantiation.shape
    extended_instantiation = numpy.pad(
        instantiation, manhattan_radius, "constant", constant_values=0
    )

    all_possible_subarrays: list[npt.NDArray[numpy.int_]] = []
    ignored_flattened_indices: list[int] = []
    considered_flattened_indices: list[int] = []
    for i in range(manhattan_radius, manhattan_radius + y):
        for j in range(manhattan_radius, manhattan_radius + x):
            # Do not generate anything if the center plaquette is 0 in the
            # original instantiation.
            if avoid_zero_plaquettes and extended_instantiation[i, j] == 0:
                ignored_flattened_indices.append(
                    (i - manhattan_radius) * x + (j - manhattan_radius)
                )
                continue
            considered_flattened_indices.append(
                (i - manhattan_radius) * x + (j - manhattan_radius)
            )
            all_possible_subarrays.append(
                extended_instantiation[
                    i - manhattan_radius : i + manhattan_radius + 1,
                    j - manhattan_radius : j + manhattan_radius + 1,
                ]
            )
    unique_situations, inverse_indices = numpy.unique(
        all_possible_subarrays, axis=0, return_inverse=True
    )

    # Note that the `inverse_indices` DO NOT include the ignored sub-templates because
    # their center was a 0 plaquette if `avoid_zero_plaquettes` is `True` so we
    # should reconstruct the full indices from `inverse_indices` and
    # `ignored_flattened_indices`.
    # By convention, the index 0 will represent the ignored sub-templates, so we
    # also have to shift the `inverse_indices` and `unique_situations` keys by 1.
    # Start by shifting by 1.
    inverse_indices += 1
    subtemplates_by_indices = {
        i + 1: situation for i, situation in enumerate(unique_situations)
    }
    if avoid_zero_plaquettes:
        final_indices = numpy.zeros((y * x,), dtype=numpy.int_)
        final_indices[ignored_flattened_indices] = 0
        final_indices[considered_flattened_indices] = inverse_indices
    else:
        final_indices = inverse_indices
    return UniqueSubTemplates(final_indices.reshape((y, x)), subtemplates_by_indices)
