from __future__ import annotations

import typing as ty
from dataclasses import dataclass
from math import floor

from tqec.exceptions import TQECException
from tqec.position import Shape2D
from tqec.templates.interval import EMPTY_INTERVAL, Interval, Intervals, R_interval


@dataclass(frozen=True)
class LinearFunction:
    """Represents a linear function.

    A linear function is fully described with a slope and an offset.
    """

    slope: float = 1.0
    offset: float = 0.0

    def __call__(self, x: float) -> float:
        """Evaluate the linear function on a given input.

        Args:
            x: the input to evaluate the linear function on.

        Returns:
            the image of x.
        """
        return self.slope * x + self.offset

    def __add__(self, other: LinearFunction | int | float) -> LinearFunction:
        """Add two linear functions and returns the result.

        This method does not modify self in-place.

        Args:
            other: the right-hand side to add to self.

        Returns:
            a new linear function instance representing `self + other`.
        """
        if isinstance(other, (int, float)):
            other = LinearFunction(0, other)
        return LinearFunction(self.slope + other.slope, self.offset + other.offset)

    def __sub__(self, other: LinearFunction | int | float) -> LinearFunction:
        """Subtract two linear functions and returns the result.

        This method does not modify self in-place.

        Args:
            other: the right-hand side to subtract to self.

        Returns:
            a new linear function instance representing `self - other`.
        """
        if isinstance(other, (int, float)):
            other = LinearFunction(0, other)
        return LinearFunction(self.slope - other.slope, self.offset - other.offset)

    def __mul__(self, other: int | float) -> LinearFunction:
        """Multiply a linear function by a scalar.

        Args:
            other: the scalar that should multiply self.

        Returns:
            a copy of `self`, scaled by the provided `other`.
        """
        return self.__rmul__(other)

    def __rmul__(self, other: int | float) -> LinearFunction:
        """Multiply a linear function by a scalar.

        Args:
            other: the scalar that should multiply self.

        Returns:
            a copy of `self`, scaled by the provided `other`.
        """
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
        """Compute the interval on which `self < other`.

        Args:
            other: the `LinearFunction` instance to compare to `self`.

        Returns:
            the interval on which `self < other` is verified.
        """
        other = LinearFunction._from(other)
        intersection = self.intersection(other)
        if intersection is None:
            return R_interval if self(0) < other(0) else EMPTY_INTERVAL

        before_intersection = int(floor(intersection)) - 1
        if self(before_intersection) < other(before_intersection):
            return Interval(
                float("-inf"), intersection, start_excluded=True, end_excluded=True
            )
        else:
            return Interval(
                intersection, float("inf"), start_excluded=True, end_excluded=True
            )

    def __le__(self, other: LinearFunction | float) -> Interval:
        """Compute the interval on which `self <= other`.

        Args:
            other: the `LinearFunction` instance to compare to `self`.

        Returns:
            the interval on which `self <= other` is verified.
        """
        other = LinearFunction._from(other)
        intersection = self.intersection(other)
        if intersection is None:
            return R_interval if self(0) <= other(0) else EMPTY_INTERVAL

        before_intersection = int(floor(intersection)) - 1
        if self(before_intersection) <= other(before_intersection):
            return Interval(
                float("-inf"), intersection, start_excluded=True, end_excluded=False
            )
        else:
            return Interval(
                intersection, float("inf"), start_excluded=False, end_excluded=True
            )

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
    separators_with_inf = [float("-inf"), *separators, float("+inf")]
    for i in range(len(separators_with_inf) - 1):
        yield Interval(
            separators_with_inf[i],
            separators_with_inf[i + 1],
            start_excluded=(i == 0),  # Exclude the first start that is float("-inf")
            end_excluded=True,
        )


def round_or_fail(f: float) -> int:
    rounded_value = int(round(f))
    if abs(f - rounded_value) > 1e-8:
        raise TQECException(f"Rounding from {f} to integer failed.")
    return rounded_value


@dataclass
class Scalable2D:
    x: LinearFunction
    y: LinearFunction

    def to_shape_2d(self, k: int) -> Shape2D:
        return Shape2D(round_or_fail(self.x(k)), round_or_fail(self.y(k)))

    def to_numpy_shape(self, k: int) -> tuple[int, int]:
        return self.to_shape_2d(k).to_numpy_shape()

    def __add__(self, other: Scalable2D) -> Scalable2D:
        if not isinstance(other, Scalable2D):
            raise TQECException(
                f"Addition between Scalable2D and {type(other).__name__} is "
                "not implemented."
            )
        return Scalable2D(self.x + other.x, self.y + other.y)


@dataclass(frozen=True)
class ScalableInterval:
    start: LinearFunction
    end: LinearFunction

    @property
    def width(self) -> LinearFunction:
        return self.end - self.start

    def is_empty(self) -> bool:
        return not (self.width < 0).is_empty()

    def non_empty_on(self) -> Intervals:
        print(f"Hello: {(self.width <= 0)}")
        return (self.width <= 0).complement()


@dataclass(frozen=True)
class ScalableBoundingBox:
    ul: Scalable2D
    br: Scalable2D
    possible_inputs: Interval = R_interval

    def __post_init__(self) -> None:
        negative_width_inputs = (self.width < 0).intersection(self.possible_inputs)
        if not negative_width_inputs.is_empty():
            raise TQECException(
                "Cannot create a bounding box that would have a negative width on "
                f"a valid input. Valid inputs are {self.possible_inputs} and the "
                f"computed width ({self.width}) is negative on {negative_width_inputs}."
            )
        negative_height_inputs = (self.height < 0).intersection(self.possible_inputs)
        if not negative_height_inputs.is_empty():
            raise TQECException(
                "Cannot create a bounding box that would have a negative height on "
                f"a valid input. Valid inputs are {self.possible_inputs} and the "
                f"computed height ({self.height}) is negative on {negative_height_inputs}."
            )

    @property
    def width(self) -> LinearFunction:
        return self.br.x - self.ul.x

    @property
    def height(self) -> LinearFunction:
        return self.br.y - self.ul.y

    @property
    def corners(self) -> tuple[Scalable2D, Scalable2D, Scalable2D, Scalable2D]:
        return (
            self.ul,
            Scalable2D(self.br.x, self.ul.y),
            self.br,
            Scalable2D(self.ul.x, self.br.y),
        )

    def inside(self, point: Scalable2D) -> tuple[Interval, Interval]:
        """Returns intervals in which the X and Y coordinates should both be
        for the provided point to be in the bounding box.

        Args:
            point: a scalable point.

        Returns:
            a tuple of intervals `(X, Y)`. The provided `point` is within `self` if
            and only if BOTH the x and y pre-images are in the return ranges.
        """
        x_condition = (self.ul.x <= point.x).intersection(point.x <= self.br.x)
        y_condition = (self.ul.y <= point.y).intersection(point.y <= self.br.y)
        return x_condition, y_condition
