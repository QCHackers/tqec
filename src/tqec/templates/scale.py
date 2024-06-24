import typing as ty
from dataclasses import dataclass

from tqec.exceptions import TQECException


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
