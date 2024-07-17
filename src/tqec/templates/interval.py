from __future__ import annotations

import math
import operator
import typing as ty
from dataclasses import dataclass

from tqec.exceptions import TQECException


@dataclass(frozen=True)
class Interval:
    start: float
    end: float
    start_excluded: bool = False
    end_excluded: bool = True

    def __post_init__(self):
        if math.isnan(self.start) or math.isnan(self.end):
            raise TQECException("Cannot create an Interval with a NaN bound.")
        if not self.start <= self.end:
            raise TQECException(
                f"Cannot create an interval with start={self.start} > end={self.end}."
            )

    def _is_over_start(self, value: float) -> bool:
        return self.start < value if self.start_excluded else self.start <= value

    def _is_below_end(self, value: float) -> bool:
        return value < self.end if self.end_excluded else value <= self.end

    @staticmethod
    def _compare_bounds(
        lhs: float,
        lhs_excluded: bool,
        rhs: float,
        rhs_excluded: bool,
        func: ty.Callable[[tuple[float, bool], tuple[float, bool]], tuple[float, bool]],
    ) -> tuple[float, bool]:
        res, res_excluded = func((lhs, lhs_excluded), (rhs, rhs_excluded))
        # Make sure that the correct exclusion boolean is picked if both intervals
        # have the same start.
        if lhs == rhs:
            res_excluded = lhs_excluded or rhs_excluded
        return res, res_excluded

    def contains(self, value: float) -> bool:
        return self._is_over_start(value) and self._is_below_end(value)

    def overlaps_with(self, other: Interval) -> bool:
        return not self.is_disjoint(other)

    def is_disjoint(self, other: Interval) -> bool:
        other_end_lt_self_start = other.end < self.start or (
            other.end == self.start and (other.end_excluded or self.start_excluded)
        )
        self_end_lt_other_start = self.end < other.start or (
            self.end == other.start and (self.end_excluded or other.start_excluded)
        )
        return other_end_lt_self_start or self_end_lt_other_start

    def is_empty(self) -> bool:
        return self.start == self.end and (self.start_excluded or self.end_excluded)

    def intersection(self, other: Interval) -> Interval:
        if self.is_disjoint(other):
            return EMPTY_INTERVAL

        start, start_excluded = Interval._compare_bounds(
            self.start, self.start_excluded, other.start, other.start_excluded, max
        )
        end, end_excluded = Interval._compare_bounds(
            self.end, self.end_excluded, other.end, other.end_excluded, min
        )
        return Interval(
            start, end, start_excluded=start_excluded, end_excluded=end_excluded
        )

    def _union_overlapping(self, other: Interval) -> Interval:
        return Interval(min(self.start, other.start), max(self.end, other.end))

    def union(self, other: Interval) -> Intervals:
        if self.is_disjoint(other):
            return Intervals([self, other])

        start, start_excluded = Interval._compare_bounds(
            self.start, self.start_excluded, other.start, other.start_excluded, min
        )
        end, end_excluded = Interval._compare_bounds(
            self.end, self.end_excluded, other.end, other.end_excluded, max
        )
        return Intervals(
            [
                Interval(
                    start, end, start_excluded=start_excluded, end_excluded=end_excluded
                )
            ]
        )

    def complement(self) -> Intervals:
        return Intervals(
            [
                Interval(
                    float("-inf"),
                    self.start,
                    start_excluded=True,
                    end_excluded=not self.start_excluded,
                ),
                Interval(
                    self.end,
                    float("inf"),
                    start_excluded=not self.end_excluded,
                    end_excluded=True,
                ),
            ]
        )

    def __repr__(self) -> str:
        return f"{'(' if self.start_excluded else '['}{self.start}, {self.end}{')' if self.end_excluded else ']'}"


EMPTY_INTERVAL = Interval(0, 0, start_excluded=True, end_excluded=True)


@dataclass(frozen=True)
class Intervals:
    """A collection of :class:`Interval` instances.

    This class stores a sorted list of mutually disjoint intervals and allow to
    manipulate them using union / intersection operations.

    Raises:
        TQECException: at construction, if any of the provided intervals overlap.
    """

    intervals: list[Interval]

    def __post_init__(self):
        # Use object.__setattr__ to change self.intervals, just like __init__ is
        # doing (see https://docs.python.org/3/library/dataclasses.html#frozen-instances).
        # This is only OK because we are in __post_init__ here, this would break the
        # purpose of the frozen=True argument given to the dataclass decorator anywhere
        # else.
        object.__setattr__(
            self,
            "intervals",
            sorted(
                [interval for interval in self.intervals if not interval.is_empty()],
                key=lambda i: i.start,
            ),
        )
        i = 1
        while i < len(self.intervals):
            lhs, rhs = self.intervals[i - 1], self.intervals[i]
            if lhs.overlaps_with(rhs):
                raise TQECException(
                    "Cannot build an Intervals instance with overlapping intervals."
                )
            if lhs.end == rhs.start and not (lhs.end_excluded and rhs.start_excluded):
                self.intervals[i - 1] = Interval(
                    lhs.start,
                    rhs.end,
                    start_excluded=lhs.start_excluded,
                    end_excluded=rhs.end_excluded,
                )
                self.intervals.pop(i)
            else:
                i += 1

    def contains(self, value: float) -> bool:
        return any(interval.contains(value) for interval in self.intervals)

    def is_empty(self) -> bool:
        return len(self.intervals) == 0

    def intersection(self, other: Interval | Intervals) -> Intervals:
        if isinstance(other, Interval):
            return Intervals(
                [interval.intersection(other) for interval in self.intervals]
            )
        # Because intersection distributes over unions, we can simply do
        # it the brute-force way:
        return Intervals(
            [si.intersection(oi) for si in self.intervals for oi in other.intervals]
        )

    def union(self, other: Interval | Intervals) -> Intervals:
        if isinstance(other, Interval):
            other = Intervals([other])
        all_intervals = sorted(self.intervals + other.intervals, key=lambda a: a.start)
        merged_intervals: list[Interval] = [all_intervals[0]]
        for interval in all_intervals[1:]:
            if merged_intervals[-1].overlaps_with(interval):
                merged_intervals[-1] = merged_intervals[-1]._union_overlapping(interval)
            else:
                merged_intervals.append(interval)
        return Intervals(merged_intervals)

    def complement(self) -> Intervals:
        if self.is_empty():
            return R_intervals
        intervals: list[Interval] = [
            Interval(
                float("-inf"),
                self.intervals[0].start,
                start_excluded=True,
                end_excluded=not self.intervals[0].start_excluded,
            )
        ]
        for i1, i2 in zip(self.intervals[:-1], self.intervals[1:]):
            intervals.append(
                Interval(
                    i1.end,
                    i2.start,
                    start_excluded=not i1.end_excluded,
                    end_excluded=not i2.start_excluded,
                )
            )
        intervals.append(
            Interval(
                self.intervals[-1].end,
                float("inf"),
                start_excluded=not self.intervals[-1].end_excluded,
                end_excluded=True,
            )
        )
        return Intervals(intervals)

    def __repr__(self) -> str:
        return " U ".join(map(str, self.intervals))


R_interval = Interval(
    float("-inf"), float("inf"), start_excluded=True, end_excluded=True
)
Rplus_interval = Interval(0, float("inf"), start_excluded=False, end_excluded=True)
R_intervals = Intervals([R_interval])
Rplus_intervals = Intervals([Rplus_interval])
