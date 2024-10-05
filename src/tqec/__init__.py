from tqec.compile import compile_block_graph

from . import (
    circuit,
    noise_models,
    plaquette,
    templates,
)
from ._version import __version__
from .circuit import (
    ScheduledCircuit,
    ScheduleException,
    annotate_detectors_automatically,
    generate_circuit,
    merge_scheduled_circuits,
)
from .exceptions import TQECException
from .noise_models import NoiseModel
from .plaquette import (
    Plaquette,
    PlaquetteQubit,
    PlaquetteQubits,
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)
from .plaquette.enums import (
    PlaquetteOrientation,
)
from .position import (
    Direction3D,
    Displacement,
    Position2D,
    Position3D,
    Shape2D,
)
from .sketchup import (
    BlockGraph,
    BlockType,
    Color3D,
    Cube,
    CubeType,
    NodeType,
    Pipe,
    PipeType,
    ZXEdge,
    ZXGraph,
    ZXNode,
    display_collada_model,
    read_block_graph_from_dae_file,
    write_block_graph_to_dae_file,
)
from .templates import LinearFunction, Template
from .templates.enums import (
    CornerPositionEnum,
    TemplateOrientation,
    TemplateRelativePositionEnum,
)
