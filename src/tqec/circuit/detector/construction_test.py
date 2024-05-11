import itertools
import pathlib

import stim
import pytest

from tqec.circuit.detector.construction import annotate_detectors_automatically
from tqec.circuit.detector.detector_util import (
    iter_stim_circuit_by_moments,
    has_measurement,
    has_reset,
)


def remove_detectors_and_shifts(circuit: stim.Circuit) -> stim.Circuit:
    new_circuit = stim.Circuit()
    for inst in circuit:
        if isinstance(inst, stim.CircuitRepeatBlock):
            new_circuit.append(
                stim.CircuitRepeatBlock(
                    repeat_count=inst.repeat_count,
                    body=remove_detectors_and_shifts(inst.body_copy()),
                )
            )
        elif inst.name != "DETECTOR" and inst.name != "SHIFT_COORDS":
            new_circuit.append(inst)
    return new_circuit


def reorder_detectors_for_equality_check(circuit: stim.Circuit) -> stim.Circuit:
    new_circuit = stim.Circuit()
    detectors = []
    for i in range(len(circuit)):
        inst = circuit[i]
        if inst.name == "DETECTOR":
            detectors.append(inst)
            if i == len(circuit) - 1 or circuit[i + 1].name != "DETECTOR":
                for detector in sorted(detectors, key=lambda d: d.gate_args_copy()):
                    new_circuit.append(detector)
                detectors = []
        elif isinstance(inst, stim.CircuitRepeatBlock):
            new_circuit.append(
                stim.CircuitRepeatBlock(
                    body=reorder_detectors_for_equality_check(inst.body_copy()),
                    repeat_count=inst.repeat_count,
                )
            )
        else:
            new_circuit.append(inst)
    return new_circuit


def replace_MR_with_M_then_R(circuit: stim.Circuit) -> stim.Circuit:
    new_circuit = stim.Circuit()
    for moment in iter_stim_circuit_by_moments(circuit):
        if isinstance(moment, stim.CircuitRepeatBlock):
            new_circuit.append(
                stim.CircuitRepeatBlock(
                    body=replace_MR_with_M_then_R(moment.body_copy()),
                    repeat_count=moment.repeat_count,
                )
            )
        elif has_measurement(moment, check_are_all_measurements=True) and has_reset(
            moment
        ):
            new_measure_moment = stim.Circuit()
            new_reset_moment = stim.Circuit()
            for inst in moment:
                if inst.name in ["MR", "MRZ"]:
                    new_measure_moment.append(
                        stim.CircuitInstruction("M", inst.targets_copy())
                    )
                    new_reset_moment.append(
                        stim.CircuitInstruction("R", inst.targets_copy())
                    )
                elif inst.name in ["MRX", "MRY"]:
                    new_measure_moment.append(
                        stim.CircuitInstruction(f"M{inst.name[2]}", inst.targets_copy())
                    )
                    new_reset_moment.append(
                        stim.CircuitInstruction(inst.name[1:], inst.targets_copy())
                    )
                else:
                    new_measure_moment.append(inst)
            new_circuit += new_measure_moment
            if new_measure_moment[-1].name != "TICK":
                new_circuit.append(stim.CircuitInstruction("TICK", []))
            new_circuit += new_reset_moment
            new_circuit.append(stim.CircuitInstruction("TICK", []))
        else:
            new_circuit += moment
    return new_circuit


def prepend_qubit_coords_for_repetition_code(circuit: stim.Circuit) -> stim.Circuit:
    new_circuit = stim.Circuit()
    for i in range(circuit.num_qubits):
        new_circuit.append(stim.CircuitInstruction("QUBIT_COORDS", [i], [i]))
    new_circuit += circuit
    return new_circuit


def load_extra_test_cases() -> list[tuple[str, stim.Circuit]]:
    cases = []
    circuits_dir = pathlib.Path(__file__).parent / "extra_test_circuits"
    for path in circuits_dir.glob("*.stim"):
        circuit_id = path.stem
        circuit = stim.Circuit.from_file(path)
        cases.append((circuit_id, circuit))
    return cases


def gen_test_cases() -> list[tuple[str, stim.Circuit]]:
    cases = []
    code_tasks = [
        # "repetition_code:memory",  # NOT WORKING FOR ROUNDS=1 or 2
        "surface_code:rotated_memory_x",
        "surface_code:rotated_memory_z",
        "surface_code:unrotated_memory_x",
        "surface_code:unrotated_memory_z",
    ]
    for code_task, distance, rounds, decompose_MR in itertools.product(
        code_tasks, (3, 5), (1, 2, 3, 11, 15), (True, False)
    ):
        circuit_id = f"{code_task}:d{distance}:r{rounds}:decomposeMR={decompose_MR}"
        circuit = reorder_detectors_for_equality_check(
            stim.Circuit.generated(
                code_task=code_task,
                distance=distance,
                rounds=rounds,
                after_clifford_depolarization=0.001,
                before_round_data_depolarization=0.005,
                after_reset_flip_probability=0.01,
                before_measure_flip_probability=0.01,
            )
        )
        if code_task.startswith("repetition_code"):
            circuit = prepend_qubit_coords_for_repetition_code(circuit)
        if decompose_MR:
            circuit = replace_MR_with_M_then_R(circuit)
        cases.append((circuit_id, circuit))

    extra_cases = load_extra_test_cases()  # Should fail due to the absence of anti-commuting grouping
    return cases
    # return extra_cases


@pytest.mark.parametrize("circuit_id, circuit", gen_test_cases())
def test_annotate_detectors_automatically(circuit_id: str, circuit: stim.Circuit):
    circuit_without_detectors = remove_detectors_and_shifts(circuit)
    circuit_automatic_detectors = reorder_detectors_for_equality_check(
        annotate_detectors_automatically(circuit_without_detectors)
    )
    assert circuit.num_detectors == circuit_automatic_detectors.num_detectors
    assert (
        circuit.get_detector_coordinates()
        == circuit_automatic_detectors.get_detector_coordinates()
    )
    dem1 = circuit.flattened().detector_error_model()
    dem2 = circuit_automatic_detectors.flattened().detector_error_model()
    assert dem1.approx_equals(dem2, atol=1e-6)


