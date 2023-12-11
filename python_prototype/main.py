from tqec.templates.scalable.square import ScalableAlternatingSquare
from tqec.plaquette.library.xxxx import XXXXPlaquette
from tqec.plaquette.library.zzzz import ZZZZPlaquette
from tqec.generation.circuit import generate_circuit

template = ScalableAlternatingSquare(4)
plaquettes = [XXXXPlaquette, ZZZZPlaquette]

circuit = generate_circuit(template, plaquettes)

print(circuit)
