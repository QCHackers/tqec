import marshal
import typing as ty
from operator import xor

from tqec.exceptions import TQECException


def default_scaling_function(k: int) -> int:
    return 2 * k


def get_fixed_scaling_function(fixed_scale: int) -> ty.Callable[[int], int]:
    return lambda _: fixed_scale


class Dimension:
    def __init__(
        self,
        initial_value: int,
        scaling_function: ty.Callable[[int], int] | None = None,
        is_fixed: bool | None = None,
    ) -> None:
        """Represent an integer dimension that may or may not be scalable

        This class helps in representing an integer dimension that can be either
        fixed (i.e., does not scale, even when `scale_to` is called) or scalable
        (i.e., scale_to modify in-place the instance).

        If the dimension is scalable, users are expected to input a function that
        will compute the dimension value from an input scale.

        Exactly one of `scaling_function` and `is_fixed` should be set, and the
        other one should be None.

        :param initial_value: initial value the Dimension instance should take.
            Can be anything, even a value that cannot be generated from the
            scale_to method in the case of a scalable Dimension.
        :param scaling_function: a function that takes exactly one integer as
            input (the scale provided to the `scale_to` method) and outputs the
            value this Dimension instance should take. If None, `is_fixed` should
            be set. If set, `is_fixed` should be None.
        :param is_fixed: if set and True, the Dimension instance is fixed and
            calling the `scale_to` method will not change the instance before
            returning it. You should use that instead of setting `scaling_function`
            to a constant function returning the fixed value, as the fixed value can
            be manually changed by the user but this class has no way to reliably
            change the corresponding `scaling_function`. If None, `scaling_function`
            should be set. If set, `scaling_function` should be None.
        """
        # If is_fixed is True, we do not want a scaling_function.
        # If is_fixed is False or None, we want a scaling function.
        if xor(scaling_function is None, bool(is_fixed)):
            raise TQECException(
                "You should provide only one of is_fixed or scaling_function. "
                "None or both is not allowed."
            )
        self._value = initial_value
        self._scaling_function = scaling_function

    def scale_to(self, k: int) -> "Dimension":
        """Scale the dimension to the provided scale k

        This method does nothing if the instance it is called on has been created
        with `is_fixed = True`. Else, it calls the `scaling_function` with the
        provided scale `k` and set the instance value to the output of this call.

        :param k: scale that should be used to set the instance value.
        :returns: self, potentially modified in-place if the instance is scalable.
        """
        if self._scaling_function is not None:
            self._value = self._scaling_function(k)
        return self

    @property
    def is_scalable(self) -> bool:
        """Returns True if the instance is scalable, else False."""
        return self._scaling_function is not None

    @property
    def value(self) -> int:
        """Returns the instance value."""
        return self._value

    @value.setter
    def value(self, other: int) -> None:
        """Sets directly the instance value."""
        self._value = other

    def to_dict(self) -> dict[str, ty.Any]:
        """Encodes the instance into a JSON-compatible dictionary."""
        ret: dict[str, ty.Any] = {"value": self._value}
        if self._scaling_function is None:
            ret |= {"fixed": True}
        else:
            ret |= {"scaling_function": marshal.dumps(self._scaling_function.func_code)}
        return ret
