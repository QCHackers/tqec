"""Implements a wrapper to standardise stim coordinate system across the code base."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StimCoordinates:
    """Wrapper around a tuple of coordinates.

    This class should be used whenever a `stim.CircuitInstruction` that expects
    arguments that are interpreted by stim as coordinates is built. This is the
    case of the `DETECTOR` instruction for example.
    """

    _ABS_TOL = 1e-10

    x: float
    y: float
    t: float | None = None

    def to_stim_coordinates(self) -> tuple[float, ...]:
        if self.t is not None:
            return (self.x, self.y, self.t)
        return (self.x, self.y)

    def __str__(self) -> str:
        return "(" + ",".join(f"{c:.2f}" for c in self.to_stim_coordinates()) + ")"

    def offset_spatially_by(self, x: float, y: float) -> StimCoordinates:
        return StimCoordinates(self.x + x, self.y + y, self.t)

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, StimCoordinates)
            and abs(self.x - value.x) < StimCoordinates._ABS_TOL
            and abs(self.y - value.y) < StimCoordinates._ABS_TOL
            and (
                (self.t is None and value.t is None)
                or (
                    self.t is not None
                    and value.t is not None
                    and abs(self.t - value.t) < StimCoordinates._ABS_TOL
                )
            )
        )

    def __lt__(self, other: StimCoordinates) -> bool:
        return self.to_stim_coordinates() < other.to_stim_coordinates()
