from __future__ import annotations

import math
import typing
from dataclasses import dataclass

from tqec.exceptions import TQECException


@dataclass(frozen=True)
class Interval:
    """A subset of the mathematical space representing real numbers: R.

    This class represents the mathematical object called interval. It stores
    two floating-point numbers representing the bounds of the interval as
    well as two booleans (one for each bound) to know if the corresponding
    bound is included in the interval or excluded from it.

    Raises:
        TQECException: if any bound is NaN.
        TQECException: if the provided `start` value is strictly larger than
            the provided `end` value.
    """

    start: float | int
    end: float | int
    start_excluded: bool = False
    end_excluded: bool = True

    def __post_init__(self) -> None:
        if math.isnan(self.start) or math.isnan(self.end):
            raise TQECException("Cannot create an Interval with a NaN bound.")
        if not self.start <= self.end:
            raise TQECException(
                f"Cannot create an interval with start={self.start} > end={self.end}."
            )

    def _is_over_start(self, value: float) -> bool:
        """Compare the provided value to `self.start`, taking into account
        `self.start_excluded`.

        This method checks if the provided value is contained in the interval that
        has the same `start` boundary as self but with +inf as end boundary.

        Args:
            value: the value to compare to start.

        Returns:
            True if `Interval(self.start, float("inf"), self.start_excluded,
            True).contains(value)`.
        """
        return self.start < value if self.start_excluded else self.start <= value

    def _is_below_end(self, value: float) -> bool:
        """Compare the provided value to `self.end`, taking into account
        `self.end_excluded`.

        This method checks if the provided value is contained in the interval that
        has the same `end` boundary as self but with -inf as start boundary.

        Args:
            value: the value to compare to end.

        Returns:
            True if `Interval(float("-inf"), self.end, True,
            self.end_excluded).contains(value)`.
        """
        return value < self.end if self.end_excluded else value <= self.end

    def contains(self, value: float) -> bool:
        """Returns `True` if `self` contains the provided value, else
        `False`."""
        return self._is_over_start(value) and self._is_below_end(value)

    def overlaps_with(self, other: Interval) -> bool:
        """Returns `True` if `self` overlaps with the provided interval, else
        `False`."""
        return not self.is_disjoint(other)

    def is_disjoint(self, other: Interval) -> bool:
        """Returns `True` if `self` does not overlap with the provided
        interval, else `False`."""
        other_end_lt_self_start = other.end < self.start or (
            other.end == self.start and (other.end_excluded or self.start_excluded)
        )
        self_end_lt_other_start = self.end < other.start or (
            self.end == other.start and (self.end_excluded or other.start_excluded)
        )
        return other_end_lt_self_start or self_end_lt_other_start

    def is_empty(self) -> bool:
        """Returns `True` if `self` is the empty interval, else `False`."""
        return self.start == self.end and (self.start_excluded or self.end_excluded)

    def intersection(self, other: Interval) -> Interval:
        """Compute and return the intersection of `self` and `other`."""
        if self.is_disjoint(other):
            return EMPTY_INTERVAL

        start, start_excluded = max(
            (self.start, self.start_excluded), (other.start, other.start_excluded)
        )
        if self.start == other.start:
            start_excluded = self.start_excluded or other.start_excluded

        end, end_excluded = min(
            (self.end, self.end_excluded), (other.end, other.end_excluded)
        )
        if self.end == other.end:
            end_excluded = self.end_excluded or other.end_excluded

        return Interval(
            start, end, start_excluded=start_excluded, end_excluded=end_excluded
        )

    def _union_overlapping(self, other: Interval) -> Interval:
        """Compute and return the union of `self` and `other` when they
        overlap."""
        return Interval(min(self.start, other.start), max(self.end, other.end))

    def union(self, other: Interval) -> Intervals:
        """Compute and return the union of `self` and `other`."""
        if self.is_disjoint(other):
            return Intervals([self, other])

        start, start_excluded = min(
            (self.start, self.start_excluded), (other.start, other.start_excluded)
        )
        if self.start == other.start:
            start_excluded = self.start_excluded and other.start_excluded

        end, end_excluded = max(
            (self.end, self.end_excluded), (other.end, other.end_excluded)
        )
        if self.end == other.end:
            end_excluded = self.end_excluded and other.end_excluded

        return Intervals(
            [
                Interval(
                    start, end, start_excluded=start_excluded, end_excluded=end_excluded
                )
            ]
        )

    def complement(self) -> Intervals:
        """Get the complement of the interval, defined as R \\ `self`."""
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
                    start_excluded=(
                        not self.end_excluded
                        or (self.start_excluded and self.start == self.end)
                    ),
                    end_excluded=True,
                ),
            ]
        )

    def __repr__(self) -> str:
        return f"{'(' if self.start_excluded else '['}{self.start}, {self.end}{')' if self.end_excluded else ']'}"

    def __add__(self, value: int | float) -> Interval:
        return Interval(
            self.start + value, self.end + value, self.start_excluded, self.end_excluded
        )

    def __sub__(self, value: int | float) -> Interval:
        return Interval(
            self.start - value, self.end - value, self.start_excluded, self.end_excluded
        )

    def iter_integers(self) -> typing.Iterable[int]:
        inclusive_start_int = int(math.ceil(self.start))
        if self.start_excluded and abs(self.start - inclusive_start_int) < 1e-8:
            inclusive_start_int += 1
        exclusive_end_int = int(math.floor(self.end)) + 1
        if self.end_excluded and abs(self.end - exclusive_end_int) < 1e-8:
            exclusive_end_int -= 1
        return range(inclusive_start_int, exclusive_end_int)


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

    def __post_init__(self) -> None:
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
        """Returns `True` if `self` contains the provided value, else
        `False`."""
        return any(interval.contains(value) for interval in self.intervals)

    def is_empty(self) -> bool:
        """Returns `True` if `self` is the empty interval, else `False`."""
        return len(self.intervals) == 0

    def intersection(self, other: Interval | Intervals) -> Intervals:
        """Compute and return the intersection of `self` and `other`."""
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
        """Compute and return the union of `self` and `other`."""
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
        """Get the complement of the interval, defined as R \\ `self`."""
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
