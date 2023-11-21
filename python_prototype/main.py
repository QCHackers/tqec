from tqec.templates.scalable.corner import ScalableCorner
from tqec.display import display

# Distance 4 corner
corner = ScalableCorner(4)
display(corner.scale_to(6))
print(corner.to_json(indent=2))
