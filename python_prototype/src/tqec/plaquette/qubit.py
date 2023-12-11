from dataclasses import dataclass

from tqec.position import Position
from tqec.enums import PlaquetteQubitType

import numpy


@dataclass
class PlaquetteQubit:
    type_: PlaquetteQubitType
    position: Position


def get_qubit_array_str(
    array: numpy.ndarray, qubit_str: str = "x", nothing_str: str = " "
) -> str:
    return "\n".join(
        "".join(qubit_str if boolean else nothing_str for boolean in line)
        for line in array
    )
