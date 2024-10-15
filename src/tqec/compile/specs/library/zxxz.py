from functools import partial

from tqec.compile.specs.base import CompiledBlockBuilder, SubstitutionBuilder
from tqec.compile.specs.library._utils import (
    default_compiled_block_builder,
    default_substitution_builder,
)
from tqec.plaquette.library.zxxz import make_zxxz_surface_code_plaquette


ZXXZ_BLOCK_BUILDER: CompiledBlockBuilder = partial(
    default_compiled_block_builder, plaquette_builder=make_zxxz_surface_code_plaquette
)

ZXXZ_SUBSTITUTION_BUILDER: SubstitutionBuilder = partial(
    default_substitution_builder, plaquette_builder=make_zxxz_surface_code_plaquette
)
