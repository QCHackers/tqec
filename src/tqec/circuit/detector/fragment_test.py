import stim

from tqec.circuit.detector.fragment import (
    Fragment,
    FragmentLoop,
    split_stim_circuit_into_fragments,
)


def test_split_stim_circuit_into_fragments():
    d = 5
    surface_code_circuit_with_mr = stim.Circuit.generated(
        code_task="surface_code:rotated_memory_x",
        distance=d,
        rounds=d,
        after_clifford_depolarization=0.001,
        after_reset_flip_probability=0.01,
        before_measure_flip_probability=0.01,
        before_round_data_depolarization=0.005,
    )
    fragments = split_stim_circuit_into_fragments(surface_code_circuit_with_mr)
    assert len(fragments) == 3
    f1, f2, f3 = fragments
    assert isinstance(f1, Fragment)
    assert isinstance(f2, FragmentLoop)
    assert isinstance(f3, Fragment)
    assert f1.circuit.num_measurements == d**2 - 1
    assert f1.circuit.num_ticks == 7
    assert len(f1.end_stabilizer_sources) == 2 * d**2 - 1
    assert len(f1.begin_stabilizer_sources) == d**2 - 1
    assert len(f1.sources_for_next_fragment) == d**2 - 1

    assert f2.repetitions == d - 1
    assert len(f2.fragments) == 1
    assert isinstance(f2.fragments[0], Fragment)
    assert f2.fragments[0].circuit[-38:-26] == f1.circuit[-25:-13]

    assert f3.circuit.num_measurements == d**2
