from typing import Literal, Protocol

from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.enums import MeasurementBasis, PlaquetteSide, ResetBasis


class PlaquetteBuilder(Protocol):
    """Protocol for functions building a `Plaquette`."""

    def __call__(
        self,
        basis: Literal["X", "Z"],
        data_initialization: ResetBasis | None = None,
        data_measurement: MeasurementBasis | None = None,
        x_boundary_orientation: Literal["HORIZONTAL", "VERTICAL"] = "HORIZONTAL",
        init_meas_only_on_side: PlaquetteSide | None = None,
    ) -> Plaquette: ...
