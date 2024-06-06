from __future__ import annotations

import bisect
import typing as ty
from dataclasses import dataclass
from math import ceil, floor, isinf

from tqec.exceptions import TQECException
from tqec.position import Shape2D


@dataclass(frozen=True)
class IntersectionResults:
    """Stores the necessary data to represent the intersection between
    two linear functions.

    Some conditions should be met by the attributes stored by this dataclass,
    and are checked just after construction:

    - `lhs` and `rhs` should either intersect on a single point or be colinear.
    - If `lhs` and `rhs` intersect on a single point `a` (that might be real) then:
        - for any integer `x < a`, `lhs(x) < rhs(x)`,
        - for any integer `x > a`, `lhs(x) > rhs(x)`.
    """

    lhs: LinearFunction
    rhs: LinearFunction
    value: float | None

    def __post_init__(self):
        if self.value is not None:
            before = int(floor(self.value)) - 1
            after = int(ceil(self.value)) + 1
            assert self.lhs(before) < self.rhs(before)
            assert self.lhs(after) > self.rhs(after)

    def is_within(self, start: int | float, end: int | float) -> bool:
        """Check if the intersection value is within the provided interval `[start, end)`.

        Args:
            start: inclusive start of the interval.
            end: exclusive end of the interval.

        Returns:
            bool: if the intersection is within the provided interval.
        """
        return self.value is not None and start <= self.value < end

    def before_intersection(self, is_min: bool) -> LinearFunction:
        return self.lhs if is_min else self.rhs

    def after_intersection(self, is_min: bool) -> LinearFunction:
        return self.rhs if is_min else self.lhs

    def get_function_on_interval(
        self, start: int | float, end: int | float, is_min: bool
    ) -> tuple[list[int], list[LinearFunction]]:
        """Get the min/max functions on the provided interval.

        Args:
            start: inclusive start of the interval.
            end: exclusive end of the interval.
            is_min: if True, the minimum functions are returned, else the
                maximum functions are.

        Returns:
            a tuple composed of 1. the list of separators that should be added
            within the provided interval (for this method, this list is either
            empty or contains one integer value) and 2. a list of LinearFunction
            that contains one more entry than the list of separators in one.
        """
        if self.value is None:
            # If the two linear functions do not intersect then the min/max one is
            # determined by their offsets (works also for equal linear functions).
            return [], [
                (min if is_min else max)((self.lhs, self.rhs), key=lambda lf: lf.offset)
            ]
        elif self.value <= start:
            # If the intersection is before the the interval, then return the function
            # that is the min/max, after the intersection (i.e., on the interval).
            return [], [self.after_intersection(is_min)]
        elif start < self.value < end:
            # ceil is used here because we require separators to be integers
            # and the end-part of the interval is exclusive, meaning that ending
            # the interval on 2.2 or 3 is equivalent (again, on integers).
            return [int(ceil(self.value))], [
                self.before_intersection(is_min),
                self.after_intersection(is_min),
            ]
        else:
            # If the intersection is after the the interval, then return the function
            # that is the min/max, before the intersection (i.e., on the interval).
            return [], [self.before_intersection(is_min)]


@dataclass(frozen=True)
class LinearFunction:
    """Represents a simple linear function with integer coefficients (slope and offset)."""

    slope: int = 1
    offset: int = 0

    def __call__(self, x: int) -> int:
        """Compute the value of the represented linear function on the provided point."""
        return self.slope * x + self.offset

    def __add__(self, other: LinearFunction) -> LinearFunction:
        """Add two linear functions."""
        return LinearFunction(self.slope + other.slope, self.offset + other.offset)

    def __sub__(self, other: LinearFunction) -> LinearFunction:
        """Subtract one linear function from another."""
        return LinearFunction(self.slope - other.slope, self.offset - other.offset)

    def __mul__(self, other: int) -> LinearFunction:
        """Multiply a linear function by a constant integer coefficient."""
        return self.__rmul__(other)

    def __rmul__(self, other: int) -> LinearFunction:
        """Multiply a linear function by a constant integer coefficient."""
        return LinearFunction(other * self.slope, other * self.offset)

    def invert(self, value: int) -> int | None:
        """Try to invert a linear function, finding the input that would result in the
        provided value, if it exists.

        Args:
            value: The value to solve for. The equation
                `self.slope * x + self.offset = value` is solved for `x`.

        Raises:
            TQECException: If the slope of the represented linear function is 0, and its
                offset is different from the provided value. In this case no solution
                exist.
            TQECException: If the resulting input is not an integer.

        Returns:
            a value `y` such that `self(y) == value`, or `None` if there is an infinity
            of valid pre-images.

        """
        if self.slope == 0:
            if self.offset == value:
                return None
            raise TQECException(
                f"Cannot invert {self}: the linear function is constant and so "
                f"has an infinite set of inverse for {self.offset} and no inverse "
                "for any other value."
            )
        offset_value = value - self.offset
        if offset_value % self.slope != 0:
            raise TQECException(
                f"{self} cannot invert exactly {value} as this would lead to "
                f"a non-integer value ({offset_value / self.slope})."
            )
        return (value - self.offset) // self.slope

    def intersection(self, other: LinearFunction) -> IntersectionResults:
        """Compute the intersection between two linear functions.

        Args:
            other: the `LinearFunction` instance to intersect with `self`.

        Returns:
            an instance of `IntersectionResults` containing the necessary
            data to know when the two `LinearFunction` instances intersect
            and which one is above/below before/after the intersection.
        """
        if self.slope == other.slope:
            # When parallel, even if equal.
            return IntersectionResults(self, other, None)

        intersection = -(other.offset - self.offset) / (other.slope - self.slope)
        if self.slope > other.slope:
            return IntersectionResults(self, other, intersection)
        else:
            return IntersectionResults(other, self, intersection)


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

    separators: list[int]
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

    def invert(self, x: int) -> int:
        """Try to find the preimage of `x`.

        Args:
            x: image of the piecewise linear function.

        Raises:
            TQECException: If no preimage could be found.
            TQECException: If multiple preimage have been found.

        Returns:
            the preimage of the provided value `x`.
        """
        possible_inverses: list[int] = []
        for (a, b), f in zip(self.intervals, self.functions):
            try:
                inv = f.invert(x)
                if inv is None:
                    # Any value is a valid inverse.
                    if isinf(a):
                        possible_inverses.append(0 if isinf(b) else int(b - 1))
                    else:
                        possible_inverses.append(int(a))
                elif a <= inv < b:
                    possible_inverses.append(inv)
            except TQECException:
                continue
        if not possible_inverses:
            raise TQECException(
                f"Could not find an inverse for {self} on the value {x}."
            )
        elif len(possible_inverses) == 1:
            return possible_inverses[0]
        else:  #  len(possible_inverses) > 1
            raise TQECException(f"Found multiple inverses for {self} on the value {x}.")

    def _functions_in_common(
        self, other: PiecewiseLinearFunction
    ) -> tuple[list[int], list[tuple[LinearFunction, LinearFunction]]]:
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
        separators: list[int] = []
        functions: list[tuple[LinearFunction, LinearFunction]] = []

        si, oi = 0, 0
        while si < len(self.separators) and oi < len(other.separators):
            self_is_below = self.separators[si] < other.separators[oi]
            separators.append(
                self.separators[si] if self_is_below else other.separators[oi]
            )
            functions.append(
                (
                    self.functions[si],
                    other.functions[oi],
                )
            )
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
        separators: list[int] = []
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
        separators: list[int] = []
        functions: list[LinearFunction] = []

        common_separators, common_functions = lhs._functions_in_common(rhs)

        # The special case of 2 linear functions (i.e., no separators):
        if not common_separators:
            f1, f2 = common_functions[0]
            intersection = f1.intersection(f2)
            additional_separators, functions_on_interval = (
                intersection.get_function_on_interval(
                    float("-inf"), float("+inf"), is_min
                )
            )
            separators.extend(additional_separators)
            functions.extend(functions_on_interval)
            return PiecewiseLinearFunction(separators, functions)

        # Compute for the first open interval (-inf, common_separators[0])
        f1, f2 = common_functions[0]
        intersection = f1.intersection(f2)
        additional_separators, functions_on_interval = (
            intersection.get_function_on_interval(
                float("-inf"), common_separators[0], is_min
            )
        )
        separators.extend(additional_separators)
        separators.append(common_separators[0])
        functions.extend(functions_on_interval)
        # Compute all the intervals with finite bounds
        for i, (start, end) in enumerate(
            zip(common_separators[:-1], common_separators[1:])
        ):
            f1, f2 = common_functions[i + 1]
            intersection = f1.intersection(f2)
            additional_separators, functions_on_interval = (
                intersection.get_function_on_interval(start, end, is_min)
            )
            separators.extend(additional_separators)
            separators.append(end)
            functions.extend(functions_on_interval)
        # Compute for the last open interval (common_separators[-1], inf)
        f1, f2 = common_functions[-1]
        intersection = f1.intersection(f2)
        additional_separators, functions_on_interval = (
            intersection.get_function_on_interval(
                common_separators[-1], float("inf"), is_min
            )
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


class Dimension:
    def __init__(
        self,
        initial_scale_parameter: int,
        scaling_function: LinearFunction | PiecewiseLinearFunction,
    ) -> None:
        """Represent an integer dimension that may or may not be scalable.

        This class helps in representing an integer dimension that can be either
        fixed (i.e., does not scale, even when `scale_to` is called) or scalable
        (i.e., `scale_to` modify in-place the instance).

        Args:
            initial_scale_parameter: initial scale that will be input to the
                specified `scaling_function` to compute the first value the
                `Dimension` instance should take.
            scaling_function: a function that takes exactly one integer as
                input (the scale provided to the `scale_to` method) and outputs the
                value this `Dimension` instance should take.
        """
        self._scaling_function = (
            scaling_function
            if isinstance(scaling_function, PiecewiseLinearFunction)
            else PiecewiseLinearFunction([], [scaling_function])
        )
        self._value = self._scaling_function(initial_scale_parameter)

    def scale_to(self, k: int) -> "Dimension":
        """Scale the dimension to the provided scale `k`.

        This method calls the `scaling_function` with the provided scale `k`
        and sets the instance value to the output of this call.

        Args:
            k: scale that should be used to set the instance value.

        Returns:
            `self`, potentially modified in-place if the instance is scalable.
        """
        self._value = self._scaling_function(k)
        return self

    @property
    def value(self) -> int:
        """Returns the instance value."""
        return self._value

    def _get_common_scale_parameter_or_raise(self, other: Dimension) -> int:
        self_value = self._scaling_function.invert(self.value)
        other_value = other._scaling_function.invert(other._value)
        # TODO: Remove that hack eventually
        if self_value == 0:
            return other_value
        if other_value == 0:
            return self_value
        # End of the hack
        if self_value != other_value:
            raise TQECException(
                f"Cannot get a common scale parameter. Computed {self_value} "
                f"and {other_value} that are not equal."
            )
        return self_value

    def __add__(self, other: Dimension) -> Dimension:
        return Dimension(
            self._get_common_scale_parameter_or_raise(other),
            self._scaling_function + other._scaling_function,
        )

    def __sub__(self, other: Dimension) -> Dimension:
        return Dimension(
            self._get_common_scale_parameter_or_raise(other),
            self._scaling_function - other._scaling_function,
        )

    def __mul__(self, other: int) -> Dimension:
        return other * self

    def __rmul__(self, other: int) -> Dimension:
        return Dimension(
            self._scaling_function.invert(self.value),
            self._scaling_function * other,
        )

    @staticmethod
    def min(lhs: Dimension, rhs: Dimension) -> Dimension:
        return Dimension(
            lhs._get_common_scale_parameter_or_raise(rhs),
            PiecewiseLinearFunction.min(lhs._scaling_function, rhs._scaling_function),
        )

    @staticmethod
    def max(lhs: Dimension, rhs: Dimension) -> Dimension:
        return Dimension(
            lhs._get_common_scale_parameter_or_raise(rhs),
            PiecewiseLinearFunction.max(lhs._scaling_function, rhs._scaling_function),
        )

    def __repr__(self) -> str:
        return f"Dimension({self._value}, {self._scaling_function})"


class FixedDimension(Dimension):
    def __init__(self, value: int) -> None:
        """A `Dimension` that does not scale."""
        super().__init__(value, LinearFunction(0, value))


@dataclass
class Scalable2D:
    x: Dimension
    y: Dimension

    def scale_to(self, k: int) -> None:
        self.x.scale_to(k)
        self.y.scale_to(k)


@dataclass
class ScalablePosition2D(Scalable2D):
    pass


@dataclass
class ScalableShape2D(Scalable2D):
    def to_numpy_shape(self) -> tuple[int, int]:
        return self.instantiate().to_numpy_shape()

    def instantiate(self) -> Shape2D:
        return Shape2D(self.x.value, self.y.value)


@dataclass
class ScalableOffset(Scalable2D):
    pass
