import typing as ty
from dataclasses import dataclass


@dataclass(frozen=True)
class LinearFunction:
    slope: int = 1
    offset: int = 0

    def __call__(self, x: int) -> int:
        return self.slope * x + self.offset

    def to_dict(self) -> dict[str, ty.Any]:
        return {"type": type(self).__name__, "slope": self.slope, "offset": self.offset}


class Dimension:
    def __init__(
        self,
        initial_scale_parameter: int,
        scaling_function: LinearFunction,
    ) -> None:
        """Represent an integer dimension that may or may not be scalable

        This class helps in representing an integer dimension that can be either
        fixed (i.e., does not scale, even when `scale_to` is called) or scalable
        (i.e., scale_to modify in-place the instance).

        :param initial_scale_parameter: initial scale that will be input to the
            specified scaling_function to compute the first value the Dimension
            instance should take.
        :param scaling_function: a function that takes exactly one integer as
            input (the scale provided to the `scale_to` method) and outputs the
            value this Dimension instance should take.
        """
        self._scaling_function = scaling_function
        self._value = self._scaling_function(initial_scale_parameter)

    def scale_to(self, k: int) -> "Dimension":
        """Scale the dimension to the provided scale k

        This method calls the `scaling_function` with the provided scale `k` and
        set the instance value to the output of this call.

        :param k: scale that should be used to set the instance value.
        :returns: self, potentially modified in-place if the instance is scalable.
        """
        self._value = self._scaling_function(k)
        return self

    @property
    def value(self) -> int:
        """Returns the instance value."""
        return self._value

    def to_dict(self) -> dict[str, ty.Any]:
        """Encodes the instance into a JSON-compatible dictionary."""
        return {
            "value": self._value,
            "scaling_function": self._scaling_function.to_dict(),
        }
