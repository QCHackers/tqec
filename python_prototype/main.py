from tqec.constructions.corner import ScalableCorner
from tqec.display import display

# Distance 4 corner
corner = ScalableCorner(4)
plaquettes = list(range(corner.expected_plaquettes_number))
display(corner.scale_to(6), *plaquettes)
print(corner.to_json(indent=2))
