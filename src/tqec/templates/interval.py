from __future__ import annotations

import math
from dataclasses import dataclass

from tqec.exceptions import TQECException


@dataclass(frozen=True)
class Interval:
    start: float
    end: float

    def __post_init__(self):
        if math.isnan(self.start) or math.isnan(self.end):
            raise TQECException("Cannot create an Interval with a NaN bound.")
        if not self.start <= self.end:
            raise TQECException(
                f"Cannot create an interval with {self.start} <= {self.end}."
            )

    def contains(self, value: float) -> bool:
        return self.start <= value < self.end

    def overlaps_with(self, other: Interval) -> bool:
        return not self.is_disjoint(other)

    def is_disjoint(self, other: Interval) -> bool:
        return other.end <= self.start or self.end <= other.start

    def _merge(self, other: Interval) -> Interval:
        if self.is_disjoint(other):
            raise TQECException("Cannot merge disjoint intervals.")
        return Interval(min(self.start, other.start), max(self.end, other.end))

    def is_empty(self) -> bool:
        return self.start == self.end

    def intersection(self, other: Interval) -> Interval:
        if self.is_disjoint(other):
            return Interval(0, 0)
        return Interval(max(self.start, other.start), min(self.end, other.end))

    def union(self, other: Interval) -> Intervals:
        if self.is_disjoint(other):
            return Intervals([self, other])
        return Intervals([self._merge(other)])

    def complement(self) -> Intervals:
        return Intervals(
            [Interval(float("-inf"), self.start), Interval(self.end, float("inf"))]
        )

    def __repr__(self) -> str:
        return f"[{self.start}, {self.end})"


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
            if self.intervals[i - 1].overlaps_with(self.intervals[i]):
                raise TQECException(
                    "Cannot build an Intervals instance with overlapping intervals."
                )
            if self.intervals[i - 1].end == self.intervals[i].start:
                self.intervals[i - 1] = Interval(
                    self.intervals[i - 1].start, self.intervals[i].end
                )
                self.intervals.pop(i)
            else:
                i += 1

    def contains(self, value: float) -> bool:
        return any(interval.contains(value) for interval in self.intervals)

    def _merge(self, other: Intervals) -> Intervals:
        all_intervals = sorted(self.intervals + other.intervals, key=lambda a: a.start)
        merged_intervals: list[Interval] = [all_intervals[0]]
        for interval in all_intervals[1:]:
            if merged_intervals[-1].overlaps_with(interval):
                merged_intervals[-1] = merged_intervals[-1]._merge(interval)
            else:
                merged_intervals.append(interval)
        return Intervals(merged_intervals)

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
        return self._merge(other)

    def complement(self) -> Intervals:
        if self.is_empty():
            return Intervals([Interval(float("-inf"), float("inf"))])
        intervals: list[Interval] = [Interval(float("-inf"), self.intervals[0].start)]
        for i1, i2 in zip(self.intervals[:-1], self.intervals[1:]):
            intervals.append(Interval(i1.end, i2.start))
        intervals.append(Interval(self.intervals[-1].end, float("inf")))
        return Intervals(intervals)

    def __repr__(self) -> str:
        return " U ".join(map(str, self.intervals))


