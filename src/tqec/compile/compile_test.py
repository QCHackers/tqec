import itertools
import pytest
from tqec.compile.compile import compile_block_graph
from tqec.circuit.detectors.construction import annotate_detectors_automatically
from tqec.compile.specs.base import BlockBuilder, SubstitutionBuilder
from tqec.compile.specs.library.css import CSS_BLOCK_BUILDER, CSS_SUBSTITUTION_BUILDER
from tqec.compile.specs.library.zxxz import (
    ZXXZ_BLOCK_BUILDER,
    ZXXZ_SUBSTITUTION_BUILDER,
)
from tqec.computation.block_graph.enums import CubeType, PipeType
from tqec.computation.block_graph.graph import BlockGraph
from tqec.noise_models.noise_model import NoiseModel
from tqec.position import Position3D
from tqec.gallery.logical_cnot import logical_cnot_block_graph


SPECS: dict[str, tuple[BlockBuilder, SubstitutionBuilder]] = {
    "CSS": (CSS_BLOCK_BUILDER, CSS_SUBSTITUTION_BUILDER),
    "ZXXZ": (ZXXZ_BLOCK_BUILDER, ZXXZ_SUBSTITUTION_BUILDER),
}


@pytest.mark.parametrize(
    ("spec", "cube_type", "k"),
    itertools.product(
        SPECS.keys(), (CubeType.ZXZ, CubeType.ZXX, CubeType.XZX, CubeType.XZZ), (1,)
    ),
)
def test_compile_single_block_memory(spec: str, cube_type: CubeType, k: int) -> None:
    d = 2 * k + 1
    g = BlockGraph("Single Block Memory Experiment")
    g.add_cube(Position3D(0, 0, 0), cube_type)
    block_builder, substitution_builder = SPECS[spec]
    observables, _ = g.get_abstract_observables()
    assert len(observables) == 1
    compiled_graph = compile_block_graph(
        g, block_builder, substitution_builder, observables
    )
    circuit = annotate_detectors_automatically(
        compiled_graph.generate_stim_circuit(
            k, noise_model=NoiseModel.uniform_depolarizing(0.001)
        )
    )
    assert circuit.num_detectors == (d**2 - 1) * d
    assert len(circuit.shortest_graphlike_error()) == d


@pytest.mark.parametrize(
    ("spec", "cube_type", "k"),
    itertools.product(
        SPECS.keys(),
        (CubeType.ZXZ, CubeType.ZXX, CubeType.XZX, CubeType.XZZ),
        (1,),
    ),
)
def test_compile_two_same_blocks_connected_in_time(
    spec: str, cube_type: CubeType, k: int
) -> None:
    d = 2 * k + 1
    g = BlockGraph("Two Same Blocks in Time Experiment")
    p1 = Position3D(1, 1, 0)
    p2 = Position3D(1, 1, 1)
    g.add_cube(p1, cube_type)
    g.add_cube(p2, cube_type)
    pipe_type = PipeType(cube_type.value[:2] + "o")
    g.add_pipe(p1, p2, pipe_type)

    block_builder, substitution_builder = SPECS[spec]
    observables, _ = g.get_abstract_observables()
    assert len(observables) == 1
    compiled_graph = compile_block_graph(
        g, block_builder, substitution_builder, observables
    )
    circuit = annotate_detectors_automatically(
        compiled_graph.generate_stim_circuit(
            k, noise_model=NoiseModel.uniform_depolarizing(0.001)
        )
    )
    dem = circuit.detector_error_model()
    assert dem.num_detectors == (d**2 - 1) * 2 * d
    assert dem.num_observables == 1
    assert len(dem.shortest_graphlike_error()) == d


@pytest.mark.parametrize(
    ("spec", "cube_pipe_type", "k"),
    itertools.product(
        SPECS.keys(),
        (
            (CubeType.ZXZ, PipeType.OXZ),
            (CubeType.ZXX, PipeType.ZOX),
            (CubeType.XZX, PipeType.OZX),
            (CubeType.XZZ, PipeType.XOZ),
        ),
        (1,),
    ),
)
def test_compile_two_same_blocks_connected_in_space(
    spec: str, cube_pipe_type: tuple[CubeType, PipeType], k: int
) -> None:
    d = 2 * k + 1
    g = BlockGraph("Two Same Blocks in Space Experiment")
    cube_type, pipe_type = cube_pipe_type
    p1 = Position3D(-1, 0, 0)
    shift = [0, 0, 0]
    shift[pipe_type.direction.axis_index] = 1
    p2 = p1.shift_by(*shift)
    g.add_cube(p1, cube_type)
    g.add_cube(p2, cube_type)
    g.add_pipe(p1, p2, pipe_type)

    block_builder, substitution_builder = SPECS[spec]
    observables, _ = g.get_abstract_observables()
    assert len(observables) == 1
    compiled_graph = compile_block_graph(
        g, block_builder, substitution_builder, observables
    )
    circuit = annotate_detectors_automatically(
        compiled_graph.generate_stim_circuit(
            k, noise_model=NoiseModel.uniform_depolarizing(0.001)
        )
    )
    dem = circuit.detector_error_model()
    assert dem.num_detectors == 2 * (d**2 - 1) + (d + 1 + 2 * (d**2 - 1)) * (d - 1)
    assert dem.num_observables == 1
    assert len(dem.shortest_graphlike_error()) == d


@pytest.mark.parametrize(
    ("spec", "cube_and_space_pipe_type", "k"),
    itertools.product(
        SPECS.keys(),
        (
            (CubeType.ZXZ, PipeType.OXZ),
            (CubeType.ZXX, PipeType.ZOX),
            (CubeType.XZX, PipeType.OZX),
            (CubeType.XZZ, PipeType.XOZ),
        ),
        (1,),
    ),
)
def test_compile_L_shape_in_space_time(
    spec: str, cube_and_space_pipe_type: tuple[CubeType, PipeType], k: int
) -> None:
    d = 2 * k + 1
    g = BlockGraph("L-shape Blocks Experiment")
    cube_type, space_pipe_type = cube_and_space_pipe_type
    time_pipe_type = PipeType(cube_type.value[:2] + "o")
    p1 = Position3D(1, 2, 0)
    space_shift = [0, 0, 0]
    space_shift[space_pipe_type.direction.axis_index] = 1
    p2 = p1.shift_by(*space_shift)
    p3 = p2.shift_by(dz=1)
    g.add_cube(p1, cube_type)
    g.add_cube(p2, cube_type)
    g.add_cube(p3, cube_type)
    g.add_pipe(p1, p2, space_pipe_type)
    g.add_pipe(p2, p3, time_pipe_type)

    block_builder, substitution_builder = SPECS[spec]
    observables, _ = g.get_abstract_observables()
    assert len(observables) == 1
    compiled_graph = compile_block_graph(
        g, block_builder, substitution_builder, observables
    )
    circuit = annotate_detectors_automatically(
        compiled_graph.generate_stim_circuit(
            k, noise_model=NoiseModel.uniform_depolarizing(0.001)
        )
    )
    dem = circuit.detector_error_model()
    assert (
        dem.num_detectors
        == 2 * (d**2 - 1) + (d + 1 + 2 * (d**2 - 1)) * (d - 1) + (d**2 - 1) * d
    )
    assert dem.num_observables == 1
    assert len(dem.shortest_graphlike_error()) == d


@pytest.mark.parametrize(
    ("spec", "support_z_basis_obs", "k"),
    itertools.product(
        SPECS.keys(),
        (True, False),
        (1,),
    ),
)
def test_compile_logical_cnot(spec: str, support_z_basis_obs: bool, k: int) -> None:
    d = 2 * k + 1
    g = logical_cnot_block_graph(support_z_basis_obs)

    block_builder, substitution_builder = SPECS[spec]
    observables, _ = g.get_abstract_observables()
    assert len(observables) == 3
    compiled_graph = compile_block_graph(
        g, block_builder, substitution_builder, observables
    )
    circuit = annotate_detectors_automatically(
        compiled_graph.generate_stim_circuit(
            k, noise_model=NoiseModel.uniform_depolarizing(0.001)
        )
    )
    dem = circuit.detector_error_model()
    assert dem.num_observables == 3
    assert len(dem.shortest_graphlike_error()) == d
