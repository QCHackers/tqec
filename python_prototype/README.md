# Proposal for code scaling -- Template solution

This Python package implements the idea I had to use templates to represent a scalable code. It is still a work in progress, but the code is able to build a corner quite easily and should be robust and generic enough to build more complex surface code shapes if necessary.

## Installation

This is a pure Python package with only regular dependencies. You should be good to go with a simple pip install:

```bash
python -m pip install -e python_prototype
# Check the installation
python -c "import tqec" # Should not output anything
```

## Usage

### Regular users

Users of the library should simply find the template they need in `tqec.templates` and play with it. For example, here is how to produce and scale a corner:

```python
from tqec.templates.scalable.corner import ScalableCorner
# Distance 4 corner
corner = ScalableCorner(4)
print(corner.build_array())
# [[ 0  0  1  0  1  0  0  0  0  0  0  0]
#  [ 2  3  2  3  2  0  0  0  0  0  0  0]
#  [ 0  2  3  2  3  5  0  0  0  0  0  0]
#  [ 2  3  2  3  2  0  0  0  0  0  0  0]
#  [ 0  2  3  2  3  5  0  0  0  0  0  0]
#  [ 2  3  2  3  2  0  0  0  0  0  0  0]
#  [ 0  2  3  2  3  6  0  7  0  7  0  0]
#  [ 2  3  2  3  8  9  8  8  9  8  9 10]
#  [ 0  2  3  8  9  8  9  9  8  9  8  0]
#  [ 2  3  8  9  8  9  8  8  9  8  9 10]
#  [ 0 11  9  8  9  8  9  9  8  9  8  0]
#  [ 0  0 12  0 12  0 12  0 12  0 12  0]]

# Distance 10 corner
print(corner.scale_to(10).build_array())
# Too large to display here

# Distance 1000 corner
print(corner.scale_to(1000).build_array())
# Too large to display here but takes less than a second
```

If the template you need is not implemented, you will have to become a power-user and head to the next section

### Power-users

Need more than what the library can provide? You are at the right place.

The backbone of the `tqec` library is a class named `TemplateOrchestrator`. It helps defining more complex templates using already defined templates. 

Here is a small example:

```python
from tqec.enums import ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF
from tqec.templates.base import TemplateWithPlaquettes
from tqec.templates.scalable.rectangle import ScalableRectangle
from tqec.templates.scalable.square import ScalableAlternatingSquare
from tqec.templates.orchestrator import TemplateOrchestrator

template_instances = [
    # Central square, containing plaquettes of types 3 and 4
    TemplateWithPlaquettes(ScalableAlternatingSquare(4), [3, 4]),
    # Top rectangle, containing plaquettes of type 1 only
    TemplateWithPlaquettes(ScalableRectangle(4, 1), [0, 1]),
    # Left rectangle, containing plaquettes of type 2 only
    TemplateWithPlaquettes(ScalableRectangle(1, 4), [2, 0]),
    # Right rectangle, containing plaquettes of type 5 only
    TemplateWithPlaquettes(ScalableRectangle(1, 4), [0, 5]),
    # Bottom rectangle, containing plaquettes of type 6 only
    TemplateWithPlaquettes(ScalableRectangle(4, 1), [0, 6]),
]
# Alias to avoid clutter
orchestrator = (
    TemplateOrchestrator(template_instances)
    .add_relation(1, ABOVE_OF, 0)
    .add_relation(2, LEFT_OF, 0)
    .add_relation(3, RIGHT_OF, 0)
    .add_relation(4, BELOW_OF, 0)
)
print(orchestrator.scale_to(4).instanciate())
# [[0 0 1 0 1 0]
#  [2 4 3 4 3 0]
#  [0 3 4 3 4 5]
#  [2 4 3 4 3 0]
#  [0 3 4 3 4 5]
#  [0 0 6 0 6 0]]
```

You have access to plenty of base-building blocks such as squares or rectangles of fixed or scalable size. Also, any instance of `TemplateOrchestrator` can be a building block, so feel free to create your own!

### Super-power-users

*Currently thinking about this section.*