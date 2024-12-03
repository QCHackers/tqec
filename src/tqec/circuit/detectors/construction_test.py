from __future__ import annotations

from pathlib import Path

import pytest
import stim

from tqecd.construction import annotate_detectors_automatically
from tqecd.exceptions import TQECDException

from tqec.circuit.detectors.utils import (
    detector_to_targets_tuple,
    push_all_detectors_to_the_end,
    remove_annotations,
)
from tqec.exceptions import TQECException

_HERE = Path(__file__).parent
_TEST_FOLDER = _HERE / "test_files"
_VALID_TEST_FOLDER = _TEST_FOLDER / "valid"
_INVALID_TEST_FOLDER = _TEST_FOLDER / "invalid"


def valid_test_circuits() -> list[tuple[str, stim.Circuit]]:
    valid_circuits: list[tuple[str, stim.Circuit]] = []
    for filepath in _VALID_TEST_FOLDER.iterdir():
        with open(filepath) as f:
            valid_circuits.append(
                (
                    filepath.name,
                    push_all_detectors_to_the_end(stim.Circuit(f.read())),
                )
            )
    return valid_circuits


def parse_invalid_circuit(text: str) -> tuple[stim.Circuit, str]:
    expected_error_message_regex_lines: list[str] = []
    circuit_str = ""
    for line in text.splitlines():
        if line.startswith("# ") and circuit_str == "":
            expected_error_message_regex_lines.append(line[2:])
        else:
            circuit_str += line + "\n"
    return stim.Circuit(circuit_str), "\n".join(expected_error_message_regex_lines)


def invalid_test_circuits() -> list[tuple[str, stim.Circuit, str]]:
    invalid_circuits: list[tuple[str, stim.Circuit, str]] = []
    for filepath in _INVALID_TEST_FOLDER.iterdir():
        with open(filepath) as f:
            file_content = f.read()
        circuit, expected_error_message_regex = parse_invalid_circuit(file_content)
        invalid_circuits.append((filepath.name, circuit, expected_error_message_regex))
    return invalid_circuits


def get_detectors_tuples_shallow(circuit: stim.Circuit) -> list[tuple[int, ...]]:
    detectors_tuples: list[tuple[int, ...]] = []
    for inst in circuit:
        if inst.name == "DETECTOR":
            assert isinstance(inst, stim.CircuitInstruction)
            detectors_tuples.append(detector_to_targets_tuple(inst))
    return detectors_tuples


@pytest.mark.parametrize("name,circuit", valid_test_circuits())
def test_valid_circuits(name: str, circuit: stim.Circuit) -> None:
    circuit_without_detectors = remove_annotations(
        circuit, frozenset(["DETECTOR", "SHIFT_COORDS"])
    )
    annotated_circuit = push_all_detectors_to_the_end(
        annotate_detectors_automatically(circuit_without_detectors)
    )

    initial_detectors = set(get_detectors_tuples_shallow(circuit))
    computed_detectors = set(get_detectors_tuples_shallow(annotated_circuit))

    missing_detectors = initial_detectors.difference(computed_detectors)
    assert not missing_detectors, "Detectors in original circuit are missing."


@pytest.mark.parametrize("name,circuit,error_message", invalid_test_circuits())
def test_invalid_circuits(name: str, circuit: stim.Circuit, error_message: str) -> None:
    circuit_without_detectors = remove_annotations(
        circuit, frozenset(["DETECTOR", "SHIFT_COORDS"])
    )
    with pytest.raises(TQECDException, match=rf"^{error_message}$"):
        annotate_detectors_automatically(circuit_without_detectors)
