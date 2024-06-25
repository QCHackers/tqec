from __future__ import annotations

import bisect
import typing as ty
from dataclasses import dataclass
from math import floor

from tqec.exceptions import TQECException
from tqec.position import Shape2D


@dataclass(frozen=True)
class LinearFunction:
    slope: int = 1
    offset: int = 0

    def __call__(self, x: int) -> int:
        return self.slope * x + self.offset

    def __add__(self, other: LinearFunction) -> LinearFunction:
        return LinearFunction(self.slope + other.slope, self.offset + other.offset)

    def __sub__(self, other: LinearFunction) -> LinearFunction:
        return LinearFunction(self.slope - other.slope, self.offset - other.offset)

    def __mul__(self, other: int) -> LinearFunction:
        return self.__rmul__(other)

    def __rmul__(self, other: int) -> LinearFunction:
        return LinearFunction(other * self.slope, other * self.offset)

    def intersection(self, other: LinearFunction) -> float | None:
        """Compute the intersection between two linear functions.
        Args:
            other: the `LinearFunction` instance to intersect with `self`.
        Returns:
            an instance of `IntersectionResults` containing the necessary
            data to know when the two `LinearFunction` instances intersect
            and which one is above/below before/after the intersection.
        """
        if self.slope == other.slope:
            return None

        return -(other.offset - self.offset) / (other.slope - self.slope)


def _linear_function_minmax(
    lhs: LinearFunction, rhs: LinearFunction, is_min: bool
) -> tuple[list[float], list[LinearFunction]]:
    intersection = lhs.intersection(rhs)
    if intersection is None:
        if lhs(0) < rhs(0):
            return [], [lhs if is_min else rhs]
        else:
            return [], [rhs if is_min else rhs]

    before_intersection = floor(intersection) - 1
    if lhs(before_intersection) < rhs(before_intersection):
        return [intersection], ([lhs, rhs] if is_min else [rhs, lhs])
    else:  # lhs(before_intersection) > rhs(before_intersection):
        return [intersection], ([rhs, lhs] if is_min else [lhs, rhs])


def _filter_on_interval(
    separators: list[float],
    functions: list[LinearFunction],
    start_inclusive: float,
    end_exclusive: float,
) -> tuple[list[float], list[LinearFunction]]:
    if not separators:
        return separators, functions

    if len(separators) > 1:
        raise TQECException("Expected one separator at most.")
    separator = separators[0]

    if separator < start_inclusive:
        return [], [functions[1]]
    elif separator >= end_exclusive:
        return [], [functions[0]]
    else:
        return separators, functions


def _get_minmax_on_interval(
    lhs: LinearFunction,
    rhs: LinearFunction,
    is_min: bool,
    start_inclusive: float,
    end_exclusive: float,
) -> tuple[list[float], list[LinearFunction]]:
    seps, funcs = _linear_function_minmax(lhs, rhs, is_min)
    return _filter_on_interval(seps, funcs, start_inclusive, end_exclusive)


@dataclass(frozen=True)
class PiecewiseLinearFunction:
    """A piecewise linear function.

    This dataclass encodes a piecewise linear function (that does not need
    to be continuous) by storing:

    - a list of `n` separators representing the `n` points at which the
      linear function encoded change and,
    - a list of `n+1` instances of `LinearFunction`, representing the linear
      functions on each of the `n+1` intervals represented by the `n` separators
      (and both -infinity and +infinity that are never stored explicitely).

    """

    separators: list[float]
    functions: list[LinearFunction]

    def __post_init__(self):
        """Check the invariants that should be met by any instance of this class.

        First, there should be one more `LinearFunction` instance than there are
        separators stored in the class.
        Secondly, separators should be sorted in increasing order.
        """
        assert len(self.separators) + 1 == len(self.functions)
        assert sorted(self.separators) == self.separators

    def __call__(self, x: int) -> int:
        """Compute the value of the piecewise linear function at point `x`.

        Args:
            x: point to compute the value of.

        Returns:
            the value taken by the represented piecewise linear function at the
            provided point.
        """
        index = bisect.bisect_left(self.separators, x)
        return self.functions[index](x)

    @property
    def intervals(self) -> ty.Iterable[tuple[int | float, int | float]]:
        """Returns the intervals on which each linear function is defined.

        Yields:
            an iterator over the interval of definition for each `LinearFunction`
            instance stored in `self`.
        """
        if not self.separators:
            yield float("-inf"), float("+inf")
            return

        yield float("-inf"), self.separators[0]
        for i in range(1, len(self.separators)):
            yield self.separators[i - 1], self.separators[i]
        yield self.separators[-1], float("inf")

    def _functions_in_common(
        self, other: PiecewiseLinearFunction
    ) -> tuple[list[float], list[tuple[LinearFunction, LinearFunction]]]:
        """Helper method to compute the common separators between two
        `PiecewiseLinearFunction` instances.

        This method returns a tuple composed of two lists:

        1. the list of separators that should be
           `sorted(set(self.separators) | set(other.separators))`.
        2. a list of pairs of `LinearFunction` instances representing the
           linear functions from `self` (in the first entry of each pair) and
           `other` (in the second entry of each pair) that appear together
           in the interval.

        These lists can then be used to easily compute binary functions between two
        `PiecewiseLinearFunction` instances.

        Args:
            other (PiecewiseLinearFunction): second instance to consider.

        Returns:
            a tuple composed of two lists
            1. the list of separators that should be
               `sorted(set(self.separators) | set(other.separators))`.
            2. a list of pairs of `LinearFunction` instances representing the
               linear functions from `self` (in the first entry of each pair) and
               `other` (in the second entry of each pair) that appear together
               in the interval.
        """
        separators: list[float] = []
        functions: list[tuple[LinearFunction, LinearFunction]] = []

        # si: self index
        # oi: other index
        si, oi = 0, 0
        while si < len(self.separators) and oi < len(other.separators):
            self_is_below = self.separators[si] < other.separators[oi]
            separators.append(
                self.separators[si] if self_is_below else other.separators[oi]
            )
            functions.append((self.functions[si], other.functions[oi]))
            if self_is_below:
                si += 1
            elif self.separators[si] == other.separators[oi]:
                si += 1
                oi += 1
            else:
                oi += 1

        if si == len(self.separators):
            for i in range(oi, len(other.separators)):
                separators.append(other.separators[i])
                functions.append((self.functions[-1], other.functions[i]))
        else:
            for i in range(si, len(self.separators)):
                separators.append(self.separators[i])
                functions.append((self.functions[i], other.functions[-1]))

        functions.append((self.functions[-1], other.functions[-1]))
        return separators, functions

    def __add__(self, other: PiecewiseLinearFunction) -> PiecewiseLinearFunction:
        separators, functions = self._functions_in_common(other)
        return PiecewiseLinearFunction(separators, [f1 + f2 for (f1, f2) in functions])

    def __sub__(self, other: PiecewiseLinearFunction) -> PiecewiseLinearFunction:
        separators, functions = self._functions_in_common(other)
        return PiecewiseLinearFunction(separators, [f1 - f2 for (f1, f2) in functions])

    def __mul__(self, other: int) -> PiecewiseLinearFunction:
        return self.__rmul__(other)

    def __rmul__(self, other: int) -> PiecewiseLinearFunction:
        return PiecewiseLinearFunction(
            self.separators, [other * f for f in self.functions]
        )

    def simplify(self) -> PiecewiseLinearFunction:
        """Reduce the number of intervals this function is defined on, if possible.

        Returns:
            a new instance with a number of separators that is lower or equal to
            the number of separators in `self`.
        """
        separators: list[float] = []
        functions: list[LinearFunction] = [self.functions[0]]

        for i in range(len(self.separators)):
            before_func = functions[-1]
            after_func = self.functions[i + 1]
            if before_func != after_func:
                separators.append(self.separators[i])
                functions.append(after_func)

        return PiecewiseLinearFunction(separators, functions)

    @staticmethod
    def _minmax(
        lhs: PiecewiseLinearFunction, rhs: PiecewiseLinearFunction, is_min: bool
    ) -> PiecewiseLinearFunction:
        """Compute the min/max between two `PiecewiseLinearFunction` instances.

        Args:
            lhs: left-hand side.
            rhs: right-hand side.
            is_min: if `True`, the minimum is computed. Else, the maximum
                is computed.

        Returns:
            a new instance of `PiecewiseLinearFunction` that represents the minimum
            or maximum of the two provided `PiecewiseLinearFunction` instances.
        """
        separators: list[float] = []
        functions: list[LinearFunction] = []

        common_separators, common_functions = lhs._functions_in_common(rhs)

        # The special case of 2 linear functions (i.e., no separators):
        if not common_separators:
            f1, f2 = common_functions[0]
            additional_separators, functions_on_interval = _linear_function_minmax(
                f1, f2, is_min
            )
            separators.extend(additional_separators)
            functions.extend(functions_on_interval)
            return PiecewiseLinearFunction(separators, functions)

        # Compute for the first open interval (-inf, common_separators[0])
        f1, f2 = common_functions[0]
        additional_separators, functions_on_interval = _get_minmax_on_interval(
            f1, f2, is_min, float("-inf"), common_separators[0]
        )
        separators.extend(additional_separators)
        separators.append(common_separators[0])
        functions.extend(functions_on_interval)
        # Compute all the intervals with finite bounds
        for i, (start, end) in enumerate(
            zip(common_separators[:-1], common_separators[1:])
        ):
            f1, f2 = common_functions[i + 1]
            additional_separators, functions_on_interval = _get_minmax_on_interval(
                f1, f2, is_min, start, end
            )
            separators.extend(additional_separators)
            separators.append(end)
            functions.extend(functions_on_interval)
        # Compute for the last open interval (common_separators[-1], inf)
        f1, f2 = common_functions[-1]
        additional_separators, functions_on_interval = _get_minmax_on_interval(
            f1, f2, is_min, common_separators[-1], float("inf")
        )

        separators.extend(additional_separators)
        functions.extend(functions_on_interval)

        return PiecewiseLinearFunction(separators, functions)

    @staticmethod
    def min(
        lhs: PiecewiseLinearFunction, rhs: PiecewiseLinearFunction
    ) -> PiecewiseLinearFunction:
        return PiecewiseLinearFunction._minmax(lhs, rhs, True)

    @staticmethod
    def max(
        lhs: PiecewiseLinearFunction, rhs: PiecewiseLinearFunction
    ) -> PiecewiseLinearFunction:
        return PiecewiseLinearFunction._minmax(lhs, rhs, False)

    @staticmethod
    def from_linear_function(function: LinearFunction) -> PiecewiseLinearFunction:
        return PiecewiseLinearFunction([], [function])


@dataclass
class Scalable2D:
    x: PiecewiseLinearFunction
    y: PiecewiseLinearFunction

    def to_numpy_shape(self, k: int) -> tuple[int, int]:
        return Shape2D(self.x(k), self.y(k)).to_numpy_shape()
