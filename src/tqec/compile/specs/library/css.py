from collections import defaultdict
from functools import partial

from tqec.compile.specs.base import CubeSpec, SpecRule
from tqec.compile.specs.library._utils import default_spec_rule
from tqec.plaquette.library.css import make_css_surface_code_plaquette

CSS_SPEC_RULES: defaultdict[CubeSpec, SpecRule] = defaultdict(
    lambda: partial(
        default_spec_rule, plaquette_builder=make_css_surface_code_plaquette
    )
)
