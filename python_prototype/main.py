from tqec.templates.scalable.corner import ScalableCorner

# Distance 4 corner
corner = ScalableCorner(4)
print(corner.scale_to(1000).build_array())
