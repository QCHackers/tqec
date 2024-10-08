"""Defines several widely used plaquettes for re-use.

This module goal is to centralise the definition of several widely used plaquettes
in order to avoid each user the hassle of re-defining their own plaquettes.
"""

from .empty import (
    empty_plaquette,
    empty_rounded_plaquette,
    empty_square_plaquette,
)

from .css_plaquette import make_css_surface_code_plaquette
