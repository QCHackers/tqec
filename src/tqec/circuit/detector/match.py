import functools
import itertools
import operator
from dataclasses import dataclass

from tqec.circuit.detector.pauli import PauliString
from tqec.circuit.detector.stabilizer import BoundaryStabilizer


@dataclass(frozen=True)
class MatchedDetector:
    """Represents an automatically computed detector."""

    coords: tuple[float, ...]
    measurement_indices: frozenset[int]


def match_boundary_stabilizers(
    begin_stabilizers: list[BoundaryStabilizer],
    end_stabilizers: list[BoundaryStabilizer],
    measurements: list[PauliString],
    resets: list[PauliString],
) -> list[MatchedDetector]:
    if all(bs.before_collapse.weight == 0 for bs in begin_stabilizers):
        measurements_offset = 0
    else:
        measurements_offset = len(begin_stabilizers)

    matched_detectors: list[MatchedDetector] = []
    commute_bs = [bs for bs in begin_stabilizers if bs.all_commute]
    commute_es = [es for es in end_stabilizers if es.all_commute]
    anticommute_bs = [bs for bs in begin_stabilizers if not bs.all_commute]
    anticommute_es = [es for es in end_stabilizers if not es.all_commute]

    # 1. match stabilizers 1-to-1 without anti-commuting collapses
    matched_detectors.extend(
        match_commute_stabilizers(commute_bs, commute_es, measurements_offset)
    )

    # 2. a set of end(begin) stabilizers that disjointedly cover the begin(end) stabilizer
    if commute_bs and commute_es:
        matched_detectors.extend(
            match_by_disjoint_cover(commute_bs, commute_es, measurements_offset)
        )
    if commute_bs and commute_es:
        matched_detectors.extend(
            match_by_disjoint_cover(commute_es, commute_bs, measurements_offset)
        )
    # 3. combine anti-commuting stabilizers
    if not ((commute_bs or anticommute_bs) and (commute_es or anticommute_es)):
        return matched_detectors
    # TODO: COMBINE ANTI-COMMUTING STABILIZERS
    return matched_detectors


def match_commute_stabilizers(
    begin_stabilizers: list[BoundaryStabilizer],
    end_stabilizers: list[BoundaryStabilizer],
    measurement_offset: int,
) -> list[MatchedDetector]:
    """Take stabilizers from two contiguous Fragments and try to match them.

    Let use the two `Fragment` instances `f1` and `f2` such that `f1` is just
    before `f2`. There is a stabilizer boundary at the interface between `f1`
    and `f2`. Considering only the stabilizers that propagated forward from
    the resets of `f1` and commuted with all the measurements they encountered
    (listed in `begin_stabilizers`) as well as the stabilizers that propagated
    backewards from the measurements of `f2` and commuted with all the resets
    they encountered (listed in `end_stabilizers`), we can try to match these
    stabilizers at the interface.
    This method performs a "dumb" matching between stabilizers, only matching
    if one stabilizer from `f1` exactly matches with one stabilizer from `f2`.

    Args:
        begin_stabilizers: Stabilizers that come from a previous `Fragment`
            instance, originated from reset instructions, propagated forward
            through the previous `Fragment` instance, and commuted with all
            the measurements they encountered.
        end_stabilizers: Stabilizers that come from the current `Fragment`
            instance, originated from measurement instructions, propagated
            backwards through the current `Fragment` instance, and commuted
            with all the resets they encountered.
        measurement_offset: TODO

    Returns:
        the list of all the detectors found.
    """
    detectors: list[MatchedDetector] = []
    begin_indices_to_remove: list[int] = []
    end_indices_to_remove: list[int] = []

    for bi, bs in enumerate(begin_stabilizers):
        for ei, es in enumerate(end_stabilizers):
            # If the stabilizers are not exactly the same, this is not a match.
            if bs.after_collapse != es.after_collapse:
                continue
            # Else, it is a match!
            detectors.append(
                MatchedDetector(
                    coords=bs.coords,
                    measurement_indices=frozenset(
                        bs.source_measurement_indices
                        | {i - measurement_offset for i in es.commute_collapse_indices}
                    ),
                )
            )
            begin_indices_to_remove.append(bi)
            end_indices_to_remove.append(ei)
            # break here because the begin stabilizer `bs` is matched and
            # will be removed, so there is no point trying to match it with
            # other end stabilizers.
            break

    # Clean-up the stabilizer lists
    for bi in sorted(begin_indices_to_remove, reverse=True):
        begin_stabilizers.pop(bi)
    for ei in sorted(end_indices_to_remove, reverse=True):
        end_stabilizers.pop(ei)
    return detectors


def _find_cover(
    target: BoundaryStabilizer,
    sources: list[BoundaryStabilizer],
) -> list[BoundaryStabilizer] | None:
    """Try to cover the provided `target` stabilizer with stabilizers from `sources`."""
    sources = [
        source
        for source in sources
        if target.after_collapse.contains(source.after_collapse)
    ]
    for number_of_stabilizers in range(len(sources), 1, -1):
        for potential_stabilizers_combination in itertools.combinations(
            sources, number_of_stabilizers
        ):
            candidate_stabilizer: PauliString = functools.reduce(
                operator.mul,
                (bs.after_collapse for bs in potential_stabilizers_combination[1:]),
                potential_stabilizers_combination[0].after_collapse,
            )
            # Do not compare directly the PauliString instances as, for the moment,
            # the __eq__ implemented does not correspond to mathematical equality.
            resulting_stabilizer = target.after_collapse * candidate_stabilizer
            if resulting_stabilizer.weight == 0:
                return list(potential_stabilizers_combination)

    return None


def match_by_disjoint_cover(
    target_stabilizers: list[BoundaryStabilizer],
    covering_stabilizers: list[BoundaryStabilizer],
    measurement_offset: int,
) -> list[MatchedDetector]:
    """Try to match stabilizers by finding a cover.

    This function will try to match each of the stabilizers found in
    `target_stabilizers` with several stabilizers from `covering_stabilizers`.
    This is a one-to-many relationship: one stabilizer from `target_stabilizers`
    will be matched to many stabilizers from `covering_stabilizers`.

    Args:
        target_stabilizers: list of stabilizers to try to separately match with
            several stabilizers from `covering_stabilizers`.
        covering_stabilizers: list of stabilizers that can be combined together to
            match with one stabilizer from `target_stabilizers`.
        measurement_offset: TODO

    Returns:
        the list of all the detectors found.
    """
    detectors: list[MatchedDetector] = []

    for target in list(target_stabilizers):
        cover = _find_cover(target, covering_stabilizers)
        if cover is None:
            continue
        if target.source_measurement_indices is not None:  # target.is_begin_stabilizer
            measurement_indices = target.source_measurement_indices | frozenset(
                i - measurement_offset
                for i in functools.reduce(
                    lambda a, b: a | b.commute_collapse_indices, cover, frozenset()
                )
            )
        else:
            measurement_indices = frozenset(
                i - measurement_offset for i in target.commute_collapse_indices
            ) | functools.reduce(
                lambda a, b: a | b.source_measurement_indices, cover, frozenset()
            )
        detectors.append(
            MatchedDetector(
                coords=target.coords,
                measurement_indices=measurement_indices,
            )
        )
        target_stabilizers.remove(target)
    return detectors
