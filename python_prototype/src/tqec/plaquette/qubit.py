from dataclasses import dataclass

from tqec.position import Position
from tqec.enums import PlaquetteQubitType

import numpy


@dataclass
class PlaquetteQubit:
    type_: PlaquetteQubitType
    position: Position
