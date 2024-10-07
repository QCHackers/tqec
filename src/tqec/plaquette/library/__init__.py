"""Defines several widely used plaquettes for re-use.

This module goal is to centralise the definition of several widely used plaquettes
in order to avoid each user the hassle of re-defining their own plaquettes.
"""

from .empty import (
    empty_plaquette,
    empty_rounded_plaquette,
    empty_square_plaquette,
)
from .initialisation import (
    xx_initialisation_plaquette,
    xxxx_initialisation_plaquette,
    zz_initialisation_plaquette,
    zzzz_initialisation_plaquette,
)
from .measurement import (
    xx_measurement_plaquette,
    xxxx_measurement_plaquette,
    zz_measurement_plaquette,
    zzzz_measurement_plaquette,
)
from .memory import (
    xx_memory_plaquette,
    xxxx_memory_plaquette,
    zz_memory_plaquette,
    zzzz_memory_plaquette,
)
