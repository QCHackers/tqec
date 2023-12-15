from tqec.display import display
from tqec.templates.scalable.square import ScalableAlternatingSquare
from tqec.constructions.qubit import ScalableQubitSquare
from tqec.plaquette.library import (
    XXXXPlaquette,
    ZZZZPlaquette,
    XXPlaquette,
    ZZPlaquette,
)
from tqec.enums import PlaquetteOrientation
from tqec.generation.circuit import generate_circuit

template = ScalableQubitSquare(4)
plaquettes = [
    XXPlaquette(PlaquetteOrientation.UP),
    ZZPlaquette(PlaquetteOrientation.LEFT),
    XXXXPlaquette(),
    ZZZZPlaquette(),
    ZZPlaquette(PlaquetteOrientation.RIGHT),
    XXPlaquette(PlaquetteOrientation.DOWN),
]

display(template)

circuit = generate_circuit(template, plaquettes)

print(circuit)
