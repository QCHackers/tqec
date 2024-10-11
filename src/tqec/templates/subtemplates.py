from __future__ import annotations

from dataclasses import dataclass

import numpy
import numpy.typing as npt

from tqec.exceptions import TQECException

SubTemplateType = npt.NDArray[numpy.int_]


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
    subtemplates: dict[int, SubTemplateType]

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
        any_subtemplate = next(iter(self.subtemplates.values()))
        height: int = any_subtemplate.shape[0]
        # height should be `2 * manhattan_radius + 1` so `height // 2` is
        # the Manhattan radius.
        return height // 2


def get_spatially_distinct_subtemplates(
    instantiation: npt.NDArray[numpy.int_],
    manhattan_radius: int = 1,
    avoid_zero_plaquettes: bool = True,
) -> UniqueSubTemplates:
    """Returns a representation of all the distinct sub-templates of the
    provided manhattan radius.

    Note:
        This function will likely be inefficient for large templates (i.e.,
        large values of `k`) or for large Manhattan radiuses, both in terms of
        memory used and computation time.

        Right now, with

        - `n` the width of the provided `instantiation` array,
        - `m` the height of the provided `instantiation` array,
        - `r` the provided Manhattan radius,

        it takes of the order of `n*m*(2*r+1)²` memory and has to sort an
        array of `n*m` elements of size `(2*r+1)²` in lexicographic order so
        require, in the worst case, `O(n*m*log(n*m)*(2*r+1)²)` runtime.

        Subclasses are invited to reimplement that method using a specialized
        algorithm (or hard-coded values) to speed things up.

        Some timings obtained on an AMD Ryzen 9 5950X:

        ```
        k = 10
        ----------------------------------------------------------------------
        radius   =         0 |         1 |         2 |         3 |         4
        time (s) =  0.000776 |  0.000992 |   0.00151 |   0.00227 |   0.00321
        ----------------------------------------------------------------------
        k = 20
        ----------------------------------------------------------------------
        radius   =         0 |         1 |         2 |         3 |         4
        time (s) =   0.00202 |   0.00356 |   0.00672 |    0.0116 |    0.0173
        ----------------------------------------------------------------------
        k = 40
        ----------------------------------------------------------------------
        radius   =         0 |         1 |         2 |         3 |         4
        time (s) =   0.00778 |    0.0156 |    0.0326 |    0.0574 |    0.0889
        ----------------------------------------------------------------------
        k = 80
        ----------------------------------------------------------------------
        radius   =         0 |         1 |         2 |         3 |         4
        time (s) =    0.0318 |    0.0706 |     0.147 |      0.27 |     0.426
        ----------------------------------------------------------------------
        k = 160
        ----------------------------------------------------------------------
        radius   =         0 |         1 |         2 |         3 |         4
        time (s) =     0.139 |     0.309 |     0.651 |      1.25 |      1.98
        ----------------------------------------------------------------------
        ```

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

    all_possible_subarrays: list[SubTemplateType] = []
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
    # Shape of the array provided to numpy.unique:
    #    (x * y, 2 * manhattan_radius + 1, 2 * manhattan_radius + 1)
    # Calling numpy.unique
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
        final_indices = inverse_indices.astype(numpy.int_)
    return UniqueSubTemplates(final_indices.reshape((y, x)), subtemplates_by_indices)


@dataclass(frozen=True)
class Unique3DSubTemplates:
    """Stores information on the sub-templates of a specific spatial radius
    present on a time concatenation of `Template` instances.

    This class is a generalization of :class:`UniqueSubTemplates` when several
    :class:`Template` instances are concatenated in time. In that case,
    sub-templates of the last (in time) :class:`Template` instance are not enough
    to represent the different "situations" that can be encountered.

    Attributes:
        subtemplate_indices: a 3-dimensional array with shape `(n, m, t)` where
            `(n, m)` is the shape of the original `Template` instantiation and
            `t` is the number of time-steps that are considered. This array
            stores **time independent** sub-template indices. The 3-dimensional
            sub-templates indices are all the entries on the third dimension,
            i.e., `t`-tuples indexed by `0<=i<n` and `0<=j<n`.
        subtemplates: a store of sub-template (values) indexed by `t`-tuples of
            integers (keys) that link the sub-template center to the original
            template instantiation thanks to `subtemplate_indices`.
    """

    subtemplate_indices: npt.NDArray[numpy.int_]
    subtemplates: dict[tuple[int, ...], SubTemplateType]

    def __post_init__(self) -> None:
        # Check that we have a 3-dimensional subtemplate_indices.
        shape = self.subtemplate_indices.shape
        if len(shape) != 3:
            raise TQECException(
                f"Expecting a 3-dimensional array but got the shape {shape} "
                f"that represents a {len(shape)}-dimensional array."
            )
        # Recover the number of timesteps and check that all the provided
        # subtemplates keys contain exactly the right number of entries.
        n, m, t = shape
        if any(len(k) != t for k in self.subtemplates.keys()):
            raise TQECException(
                f"Found {t} time slices in subtemplate_indices but got a key "
                f"in self.subtemplates that do not contain {t} entries."
            )
        # We do not need a valid subtemplate for the 0 index, but check that
        # all the other indices have their corresponding entry.
        zero = tuple(0 for _ in range(t))
        indices: frozenset[tuple[int, ...]] = frozenset(
            tuple(arr)
            for arr in numpy.unique(self.subtemplate_indices.reshape(n * m, t), axis=0)
        ) - {zero}
        if not indices.issubset(self.subtemplates.keys()):
            raise TQECException(
                "Found an index in subtemplate_indices that does "
                "not correspond to a valid subtemplate."
            )
        # Check that the provided subtemplate shapes are valid:
        # - square with odd sides in the spatial dimensions,
        # - 3-dimensional
        # - all equal
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
        if len(shape) != 3:
            raise TQECException(
                "Expecting 3-dimensional subtemplates but got a template with "
                f"{len(shape)} dimensions."
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
        any_subtemplate = next(iter(self.subtemplates.values()))
        height: int = any_subtemplate.shape[0]
        # height should be `2 * manhattan_radius + 1` so `height // 2` is
        # the Manhattan radius.
        return height // 2


def get_spatially_distinct_3d_subtemplates(
    instantiations: tuple[npt.NDArray[numpy.int_], ...],
    manhattan_radius: int = 1,
    avoid_zero_plaquettes: bool = True,
) -> Unique3DSubTemplates:
    unique_2d_subtemplates = [
        get_spatially_distinct_subtemplates(
            inst,
            manhattan_radius=manhattan_radius,
            avoid_zero_plaquettes=avoid_zero_plaquettes,
        )
        for inst in instantiations
    ]

    subtemplates_indices = numpy.stack(
        [u2ds.subtemplate_indices for u2ds in unique_2d_subtemplates], axis=2
    )
    n, m, t = subtemplates_indices.shape
    subtemplates: dict[tuple[int, ...], npt.NDArray[numpy.int_]] = {}

    unique_3d_indices = numpy.unique(subtemplates_indices.reshape(n * m, t), axis=0)
    # We might have 0 indices on some 2-dimensional slices. Because 0 will not be
    # a valid index for the 2-dimensional subtemplates we got from
    # get_spatially_distinct_subtemplates, pre-generate the corresponding array.
    zeros_2d = numpy.zeros(
        (2 * manhattan_radius + 1, 2 * manhattan_radius + 1), dtype=numpy.int_
    )
    for indices in unique_3d_indices:
        if all(i == 0 for i in indices):
            continue
        # Get the list of subtemplates that should be stacked in the time dimension.
        subtemplates_2d_to_stack: list[npt.NDArray[numpy.int_]] = []
        for t, i in enumerate(indices):
            if i == 0:
                subtemplates_2d_to_stack.append(zeros_2d)
            else:
                subtemplates_2d_to_stack.append(
                    unique_2d_subtemplates[t].subtemplates[i]
                )
        # Stack the 2-dimensional subtemplates into a 3-dimensional one.
        subtemplate = numpy.stack(subtemplates_2d_to_stack, axis=2)
        # Add the 3-dimensional subtemplate to the mapping.
        subtemplates[tuple(indices)] = subtemplate
    return Unique3DSubTemplates(subtemplates_indices, subtemplates)
