from __future__ import annotations

import bisect
import operator
import typing as ty
from dataclasses import dataclass
from math import floor

from tqec.enums import Axis
from tqec.exceptions import TQECException
from tqec.position import Shape2D
from tqec.templates.interval import Interval, Intervals, R_interval


@dataclass(frozen=True)
class LinearFunction:
    slope: float = 1.0
    offset: float = 0.0

    def __call__(self, x: float) -> float:
        return self.slope * x + self.offset

    def __add__(self, other: LinearFunction | int | float) -> LinearFunction:
        if isinstance(other, (int, float)):
            other = LinearFunction(0, other)
        return LinearFunction(self.slope + other.slope, self.offset + other.offset)

    def __sub__(self, other: LinearFunction | int | float) -> LinearFunction:
        if isinstance(other, (int, float)):
            other = LinearFunction(0, other)
        return LinearFunction(self.slope - other.slope, self.offset - other.offset)

    def __mul__(self, other: int | float) -> LinearFunction:
        return self.__rmul__(other)

    def __rmul__(self, other: int | float) -> LinearFunction:
        return LinearFunction(other * self.slope, other * self.offset)

    def intersection(self, other: LinearFunction) -> float | None:
        """Compute the intersection between two linear functions.
        Args:
            other: the `LinearFunction` instance to intersect with `self`.
        Returns:
            If they intersect, return x such that `self(x) = other(x)`.
            Otherwise, return None.
        """
        if self.slope == other.slope:
            return None

        return -(other.offset - self.offset) / (other.slope - self.slope)

    def __lt__(self, other: LinearFunction | float) -> Interval:
        other = LinearFunction._from(other)
        intersection = self.intersection(other)
        if intersection is None:
            if self(0) < other(0):
                return Interval(float("-inf"), float("inf"))
            else:
                return Interval(0, 0)

        before_intersection = int(floor(intersection)) - 1
        if self(before_intersection) < other(before_intersection):
            return Interval(float("-inf"), intersection)
        else:
            return Interval(intersection, float("inf"))

    def __le__(self, other: LinearFunction | float) -> Interval:
        other = LinearFunction._from(other)
        if self == other:
            return Interval(float("-inf"), float("inf"))
        return self < other

    @staticmethod
    def _from(obj: LinearFunction | float) -> LinearFunction:
        if isinstance(obj, (float, int)):
            return LinearFunction(0, obj)
        else:
            return obj

    def __repr__(self) -> str:
        if abs(self.slope) < 1e-8:
            return str(self.offset)
        if abs(self.offset) < 1e-8:
            return f"{self.slope}*x"
        return f"{self.slope}*x + {self.offset}"


def _linear_function_minmax(
    lhs: LinearFunction, rhs: LinearFunction, is_min: bool
) -> tuple[list[float], list[LinearFunction]]:
    intersection = lhs.intersection(rhs)
    if intersection is None:
        if lhs(0) < rhs(0):
            return [], [lhs if is_min else rhs]
        else:
            return [], [rhs if is_min else lhs]

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


def intervals_from_separators(separators: list[float]) -> ty.Iterator[Interval]:
    if not separators:
        yield Interval(float("-inf"), float("+inf"))
        return

    yield Interval(float("-inf"), separators[0])
    for i in range(1, len(separators)):
        yield Interval(separators[i - 1], separators[i])
    yield Interval(separators[-1], float("inf"))


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

    def __call__(self, x: int | float) -> int | float:
        """Compute the value of the piecewise linear function at point `x`.

        Args:
            x: point to compute the value of.

        Returns:
            the value taken by the represented piecewise linear function at the
            provided point.
        """
        index = bisect.bisect_left(self.separators, x)
        return self.functions[index](x)

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

    def __add__(self, other: PiecewiseLinearFunction | int) -> PiecewiseLinearFunction:
        if isinstance(other, int):
            return PiecewiseLinearFunction(
                self.separators, [f + other for f in self.functions]
            )
        separators, functions = self._functions_in_common(other)
        return PiecewiseLinearFunction(separators, [f1 + f2 for (f1, f2) in functions])

    def __sub__(self, other: PiecewiseLinearFunction | int) -> PiecewiseLinearFunction:
        if isinstance(other, int):
            return PiecewiseLinearFunction(
                self.separators, [f - other for f in self.functions]
            )
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

    def _restrict_on_positive_inputs(self) -> PiecewiseLinearFunction:
        index = bisect.bisect_right(self.separators, 0)
        return PiecewiseLinearFunction(self.separators[index:], self.functions[index:])

    def simplify_positive(self) -> PiecewiseLinearFunction:
        return self._restrict_on_positive_inputs().simplify()

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

    @staticmethod
    def _from(
        obj: PiecewiseLinearFunction | LinearFunction | float,
    ) -> PiecewiseLinearFunction:
        if isinstance(obj, (float, int)):
            return PiecewiseLinearFunction.from_linear_function(LinearFunction(0, obj))
        elif isinstance(obj, LinearFunction):
            return PiecewiseLinearFunction.from_linear_function(obj)
        else:
            return obj

    @staticmethod
    def _comparison(
        lhs: PiecewiseLinearFunction | LinearFunction | float,
        rhs: PiecewiseLinearFunction | LinearFunction | float,
        operator: ty.Callable[[LinearFunction, LinearFunction], Interval],
    ) -> Intervals:
        lhs = PiecewiseLinearFunction._from(lhs)
        rhs = PiecewiseLinearFunction._from(rhs)

        result_intervals: list[Interval] = []
        common_separators, common_functions = lhs._functions_in_common(rhs)
        intervals = intervals_from_separators(common_separators)
        for interval, (lhs_f, rhs_f) in zip(intervals, common_functions):
            result_intervals.append(interval.intersection(operator(lhs_f, rhs_f)))
        return Intervals(result_intervals)

    def __lt__(
        self, other: PiecewiseLinearFunction | LinearFunction | float
    ) -> Intervals:
        return PiecewiseLinearFunction._comparison(self, other, operator.lt)

    def __le__(
        self, other: PiecewiseLinearFunction | LinearFunction | float
    ) -> Intervals:
        return PiecewiseLinearFunction._comparison(self, other, operator.le)

    def __repr__(self) -> str:
        piecewise_representations: list[str] = []
        for interval, function in zip(
            intervals_from_separators(self.separators), self.functions
        ):
            piecewise_representations.append(
                f"[{interval.start}  {function}  {interval.end})"
            )
        return (
            self.__class__.__name__ + "(" + ", ".join(piecewise_representations) + ")"
        )


def round_or_fail(f: float) -> int:
    rounded_value = int(f)
    if abs(f - rounded_value) > 1e-8:
        raise TQECException(f"Rounding from {f} to integer failed.")
    return rounded_value


@dataclass
class Scalable2D:
    x: PiecewiseLinearFunction
    y: PiecewiseLinearFunction

    def to_shape_2d(self, k: int) -> Shape2D:
        return Shape2D(round_or_fail(self.x(k)), round_or_fail(self.y(k)))

    def to_numpy_shape(self, k: int) -> tuple[int, int]:
        return self.to_shape_2d(k).to_numpy_shape()

    def simplify(self) -> Scalable2D:
        return Scalable2D(self.x.simplify(), self.y.simplify())

    def simplify_positive(self) -> Scalable2D:
        return Scalable2D(self.x.simplify_positive(), self.y.simplify_positive())

    def __add__(self, other: Scalable2D) -> Scalable2D:
        if not isinstance(other, Scalable2D):
            raise TQECException(
                f"Addition between Scalable2D and {type(other).__name__} is "
                "not implemented."
            )
        return Scalable2D(self.x + other.x, self.y + other.y)


@dataclass(frozen=True)
class ScalableInterval:
    start: PiecewiseLinearFunction
    end: PiecewiseLinearFunction

    @property
    def width(self) -> PiecewiseLinearFunction:
        return self.end - self.start

    def is_empty(self) -> bool:
        return not (self.width < 0).is_empty()

    def intersection(self, other: ScalableInterval) -> ScalableInterval:
        return ScalableInterval(
            PiecewiseLinearFunction.max(self.start, other.start),
            PiecewiseLinearFunction.min(self.end, other.end),
        )

    def non_empty_on(self) -> Intervals:
        return (self.width <= 0).complement()


@dataclass(frozen=True)
class ScalableBoundingBox:
    ul: Scalable2D
    br: Scalable2D
    possible_inputs: Intervals = R_interval

    def __post_init__(self):
        negative_width_inputs = (self.width <= 0).intersection(self.possible_inputs)
        if not negative_width_inputs.is_empty():
            raise TQECException(
                "Cannot create a bounding box that would have a negative width on "
                f"a valid input. Valid inputs are {self.possible_inputs} and the "
                f"computed width ({self.width}) is negative on {negative_width_inputs}."
            )
        negative_height_inputs = (self.height <= 0).intersection(self.possible_inputs)
        if not negative_height_inputs.is_empty():
            raise TQECException(
                "Cannot create a bounding box that would have a negative height on "
                f"a valid input. Valid inputs are {self.possible_inputs} and the "
                f"computed height ({self.height}) is negative on {negative_height_inputs}."
            )

    @property
    def width(self) -> PiecewiseLinearFunction:
        return self.br.x - self.ul.x

    @property
    def height(self) -> PiecewiseLinearFunction:
        return self.br.y - self.ul.y

    @property
    def corners(self) -> tuple[Scalable2D, Scalable2D, Scalable2D, Scalable2D]:
        return (
            self.ul,
            Scalable2D(self.br.x, self.ul.y),
            self.br,
            Scalable2D(self.ul.x, self.br.y),
        )

    def inside(self, point: Scalable2D) -> tuple[Intervals, Intervals]:
        """Returns intervals in which the X and Y coordinates should both be for the
        provided point to be in the bounding box.

        Args:
            point: a scalable point.

        Returns:
            a tuple of intervals `(X, Y)`. The provided `point` is within `self` if
            and only if BOTH the x and y pre-images are in the return ranges.
        """
        x_condition = (self.ul.x <= point.x).intersection(point.x <= self.br.x)
        y_condition = (self.ul.y <= point.y).intersection(point.y <= self.br.y)
        return x_condition, y_condition

    def _on_axis(self, axis: Axis) -> ScalableInterval:
        if axis == Axis.X:
            return ScalableInterval(self.ul.x, self.br.x)
        elif axis == Axis.Y:
            return ScalableInterval(self.ul.y, self.br.y)
        else:
            raise TQECException(f"Axis {axis} not implemented.")

    def intersect(self, other: ScalableBoundingBox) -> tuple[Intervals, Intervals]:
        x_axis_projection_intersection = (
            self._on_axis(Axis.X).intersection(other._on_axis(Axis.X)).non_empty_on()
        )
        y_axis_projection_intersection = (
            self._on_axis(Axis.Y).intersection(other._on_axis(Axis.Y)).non_empty_on()
        )
        return x_axis_projection_intersection, y_axis_projection_intersection
