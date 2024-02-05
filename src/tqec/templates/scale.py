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
        if self._scaling_function is not None:
            self._value = self._scaling_function(k)
        return self

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, other: int) -> None:
        self._value = other

    def to_dict(self) -> dict[str, ty.Any]:
        ret: dict[str, ty.Any] = {"value": self._value}
        if self._scaling_function is None:
            ret |= {"fixed": True}
        else:
            ret |= {"scaling_function": marshal.dumps(self._scaling_function.func_code)}
        return ret


class FixedDimension(Dimension):
    def __init__(
        self,
        initial_value: int,
    ) -> None:
        super().__init__(initial_value, lambda k: initial_value)
