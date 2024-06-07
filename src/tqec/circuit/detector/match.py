import functools
import itertools
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

    matched_detectors = []
    commute_bs = [bs for bs in begin_stabilizers if bs.all_commute]
    commute_es = [es for es in end_stabilizers if es.all_commute]
    anticommute_bs = [bs for bs in begin_stabilizers if not bs.all_commute]
    anticommute_es = [es for es in end_stabilizers if not es.all_commute]

    # 1. match stabilizers without anti-commuting collapses
    match_commute_stabilizers(
        commute_bs, commute_es, measurements_offset, matched_detectors
    )

    # 2. a set of end(begin) stabilizers that disjointedly cover the begin(end) stabilizer
    if commute_bs and commute_es:
        match_by_disjoint_cover(
            commute_bs, commute_es, measurements_offset, matched_detectors
        )
    if commute_bs and commute_es:
        match_by_disjoint_cover(
            commute_es, commute_bs, measurements_offset, matched_detectors
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
    detectors_out: list[MatchedDetector],
) -> None:
    for bs in list(begin_stabilizers):
        for es in list(end_stabilizers):
            if bs.after_collapse != es.after_collapse:
                continue
            detectors_out.append(
                MatchedDetector(
                    coords=bs.coords,
                    measurement_indices=frozenset(
                        bs.source_measurement_indices
                        | {i - measurement_offset for i in es.commute_collapse_indices}
                    ),
                )
            )
            begin_stabilizers.remove(bs)
            end_stabilizers.remove(es)
            break


def find_cover(
    target: BoundaryStabilizer,
    sources: list[BoundaryStabilizer],
) -> list[BoundaryStabilizer] | None:
    subsets = [
        source
        for source in sources
        if target.after_collapse.contains(source.after_collapse)
    ]
    for n in range(len(subsets), 1, -1):
        for comb in itertools.combinations(subsets, n):
            if (
                functools.reduce(
                    lambda a, b: a * b.after_collapse,
                    comb,
                    PauliString(dict()),
                )
                == target.after_collapse
            ):
                return list(comb)
            elif (
                functools.reduce(
                    lambda a, b: a * b.after_collapse, comb, target.after_collapse
                ).weight
                == 0
            ):
                return list(comb)
    return None


def match_by_disjoint_cover(
    target_stabilizers: list[BoundaryStabilizer],
    covering_stabilizers: list[BoundaryStabilizer],
    measurement_offset: int,
    detectors_out: list[MatchedDetector],
) -> None:
    for target in list(target_stabilizers):
        subsets = find_cover(target, covering_stabilizers)
        if subsets is None:
            continue
        if target.source_measurement_indices is not None:  # target.is_begin_stabilizer
            measurement_indices = target.source_measurement_indices | frozenset(
                i - measurement_offset
                for i in functools.reduce(
                    lambda a, b: a | b.commute_collapse_indices, subsets, frozenset()
                )
            )
        else:
            measurement_indices = frozenset(
                i - measurement_offset for i in target.commute_collapse_indices
            ) | functools.reduce(
                lambda a, b: a | b.source_measurement_indices, subsets, frozenset()
            )
        detectors_out.append(
            MatchedDetector(
                coords=target.coords,
                measurement_indices=measurement_indices,
            )
        )
        target_stabilizers.remove(target)
