from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RGBA:
    r: int
    g: int
    b: int
    a: float

    def with_alpha(self, a: float) -> RGBA:
        return RGBA(self.r, self.g, self.b, a)

    def as_floats(self) -> tuple[float, float, float, float]:
        return (self.r / 255, self.g / 255, self.b / 255, self.a)

    @staticmethod
    def x_color() -> RGBA:
        return RGBA(255, 127, 127, 1.0)

    @staticmethod
    def y_color() -> RGBA:
        return RGBA(99, 198, 118, 1.0)

    @staticmethod
    def z_color() -> RGBA:
        return RGBA(115, 150, 255, 1.0)

    @staticmethod
    def h_color() -> RGBA:
        return RGBA(255, 255, 101, 1.0)

    @staticmethod
    def x_correlation_color() -> RGBA:
        return RGBA(255, 0, 0, 0.8)

    @staticmethod
    def z_correlation_color() -> RGBA:
        return RGBA(0, 0, 255, 0.8)
