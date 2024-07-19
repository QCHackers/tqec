from copy import deepcopy
from dataclasses import dataclass

from tqec.web.plaquettes.library import PREDEFINED_PLAQUETTES_LIBRARY, PlaquetteLibrary
from tqec.web.templates.library import PREDEFINED_TEMPLATES_LIBRARY, TemplateLibrary


@dataclass
class UserSession:
    plaquette_library: PlaquetteLibrary = deepcopy(PREDEFINED_PLAQUETTES_LIBRARY)
    template_library: TemplateLibrary = deepcopy(PREDEFINED_TEMPLATES_LIBRARY)
