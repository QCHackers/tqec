import numpy
import numpy.typing as npt


def get_spatially_distinct_subtemplates(
    instantiation: npt.NDArray[numpy.int_],
    manhattan_radius: int = 1,
    avoid_zero_plaquettes: bool = True,
) -> tuple[npt.NDArray[numpy.int_], dict[int, npt.NDArray[numpy.int_]]]:
    """Returns a representation of all the distinct sub-templates of the
    provided manhattan radius.

    This method filters out any

    Note:
        This method will likely be inefficient for large templates (i.e., large
        values of `k`) or for large manhattan radiuses, both in terms of memory
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
        a tuple containing:

        1. an array that has the exact same shape as `self.instantiate()`
            but that is filled with indices from the second part of this
            tuple.
        2. a mapping from indices to the corresponding sub-template.
    """
    y, x = instantiation.shape
    vzeros = numpy.zeros((y + 2 * manhattan_radius, manhattan_radius), dtype=numpy.int_)
    hzeros = numpy.zeros((manhattan_radius, x), dtype=numpy.int_)
    extended_instantiation = numpy.hstack(
        (vzeros, numpy.vstack((hzeros, instantiation, hzeros)), vzeros)
    )

    all_possible_subarrays: list[npt.NDArray[numpy.int_]] = []
    for i in range(manhattan_radius, manhattan_radius + y):
        for j in range(manhattan_radius, manhattan_radius + x):
            # Do not generate anything if the center plaquette is 0 in the
            # original instantiation.
            if avoid_zero_plaquettes and extended_instantiation[i, j] == 0:
                continue
            all_possible_subarrays.append(
                extended_instantiation[
                    i - manhattan_radius : i + manhattan_radius + 1,
                    j - manhattan_radius : j + manhattan_radius + 1,
                ]
            )
    unique_situations, inverse_indices = numpy.unique(
        all_possible_subarrays, axis=0, return_inverse=True
    )

    situations = inverse_indices.reshape((y, x))
    subtemplates_by_indices = dict(enumerate(unique_situations))

    return situations, subtemplates_by_indices
