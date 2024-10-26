from __future__ import annotations

from dataclasses import dataclass

from tqec.interop.geometry import FaceKind


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


DEFAULT_FACE_COLORS: dict[FaceKind, RGBA] = {
    FaceKind.X: RGBA(255, 127, 127, 1.0),
    FaceKind.Y: RGBA(99, 198, 118, 1.0),
    FaceKind.Z: RGBA(115, 150, 255, 1.0),
    FaceKind.H: RGBA(255, 255, 101, 1.0),
    FaceKind.X_CORRELATION: RGBA(255, 0, 0, 0.5),
    FaceKind.Z_CORRELATION: RGBA(0, 0, 255, 0.5),
}
