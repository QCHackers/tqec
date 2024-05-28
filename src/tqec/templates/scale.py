from __future__ import annotations

import bisect
import typing as ty
from dataclasses import dataclass
from math import ceil, floor

from tqec.exceptions import TQECException
from tqec.position import Shape2D


@dataclass(frozen=True)
class IntersectionResults:
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
        return self.value is not None and start <= self.value < end

    def before_intersection(self, is_min: bool) -> LinearFunction:
        return self.lhs if is_min else self.rhs

    def after_intersection(self, is_min: bool) -> LinearFunction:
        return self.rhs if is_min else self.lhs

    def get_function_on_interval(
        self, start: int | float, end: int | float, is_min: bool
    ) -> tuple[list[int], list[LinearFunction]]:
        if self.value is None:
            return [], [
                (min if is_min else max)((self.lhs, self.rhs), key=lambda lf: lf.offset)
            ]
        elif self.value <= start:
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
            return [], [self.before_intersection(is_min)]


@dataclass(frozen=True)
class LinearFunction:
    slope: int = 1
    offset: int = 0

    def __call__(self, x: int) -> int:
        return self.slope * x + self.offset

    def to_dict(self) -> dict[str, ty.Any]:
        return {"type": type(self).__name__, "slope": self.slope, "offset": self.offset}

    def __add__(self, other: "LinearFunction") -> "LinearFunction":
        return LinearFunction(self.slope + other.slope, self.offset + other.offset)

    def __sub__(self, other: "LinearFunction") -> "LinearFunction":
        return LinearFunction(self.slope - other.slope, self.offset - other.offset)

    def __mul__(self, other: int) -> "LinearFunction":
        return self.__rmul__(other)

    def __rmul__(self, other: int) -> "LinearFunction":
        return LinearFunction(other * self.slope, other * self.offset)

    def invert(self, value: int) -> int:
        if self.slope == 0:
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
    separators: list[int]
    functions: list[LinearFunction]

    def __post_init__(self):
        assert len(self.separators) + 1 == len(self.functions)
        assert sorted(self.separators) == self.separators

    def __call__(self, x: int) -> int:
        index = bisect.bisect_left(self.separators, x)
        return self.functions[index](x)

    def invert(self, x: int) -> int:
        index = bisect.bisect_left(self.separators, x)
        return self.functions[index].invert(x)

    def _functions_in_common(
        self, other: PiecewiseLinearFunction
    ) -> tuple[list[int], list[tuple[LinearFunction, LinearFunction]]]:
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
        fixed (i.e., does not scale, even when ``scale_to`` is called) or scalable
        (i.e., ``scale_to`` modify in-place the instance).

        Args:
            initial_scale_parameter: initial scale that will be input to the
                specified ``scaling_function`` to compute the first value the
                ``Dimension`` instance should take.
            scaling_function: a function that takes exactly one integer as
                input (the scale provided to the ``scale_to`` method) and outputs the
                value this ``Dimension`` instance should take.
        """
        self._scaling_function = (
            scaling_function
            if isinstance(scaling_function, PiecewiseLinearFunction)
            else PiecewiseLinearFunction([], [scaling_function])
        )
        self._value = self._scaling_function(initial_scale_parameter)

    def scale_to(self, k: int) -> "Dimension":
        """Scale the dimension to the provided scale ``k``.

        This method calls the ``scaling_function`` with the provided scale ``k``
        and sets the instance value to the output of this call.

        Args:
            k: scale that should be used to set the instance value.

        Returns:
            ``self``, potentially modified in-place if the instance is scalable.
        """
        self._value = self._scaling_function(k)
        return self

    @property
    def value(self) -> int:
        """Returns the instance value."""
        return self._value

    def __add__(self, other: Dimension) -> Dimension:
        return Dimension(
            self._scaling_function.invert(self.value),
            self._scaling_function + other._scaling_function,
        )

    def __sub__(self, other: Dimension) -> Dimension:
        return Dimension(
            self._scaling_function.invert(self.value),
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
        lhs_initial_value = lhs._scaling_function.invert(lhs.value)
        rhs_initial_value = rhs._scaling_function.invert(rhs.value)
        assert lhs_initial_value == rhs_initial_value, "Limitation for the moment."

        return Dimension(
            lhs_initial_value,
            PiecewiseLinearFunction.min(lhs._scaling_function, rhs._scaling_function),
        )

    @staticmethod
    def max(lhs: Dimension, rhs: Dimension) -> Dimension:
        lhs_initial_value = lhs._scaling_function.invert(lhs.value)
        rhs_initial_value = rhs._scaling_function.invert(rhs.value)
        assert lhs_initial_value == rhs_initial_value, "Limitation for the moment."

        return Dimension(
            lhs_initial_value,
            PiecewiseLinearFunction.max(lhs._scaling_function, rhs._scaling_function),
        )


class FixedDimension(Dimension):
    def __init__(self, value: int) -> None:
        """A ``Dimension`` that does not scale."""
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
