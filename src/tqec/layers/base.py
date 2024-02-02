import numbers

import cirq
from tqec.detectors.gate import ShiftCoordsGate
from tqec.generation.circuit import generate_circuit
from tqec.plaquette.plaquette import Plaquette
from tqec.position import Position
from tqec.templates.base import Template


def make_repeated_layer(
    circuit: cirq.Circuit, repetitions: int, add_shift_coord_gate: bool
) -> cirq.Circuit:
    circuit_to_repeat = circuit
    if add_shift_coord_gate:
        # Note: we do not care on which qubit it is applied, but we want a SHIFT_COORDS instruction
        #       to be inserted somewhere in the repetition loop. It is inserted at the beginning.
        any_qubit = next(iter(circuit.all_qubits()), None)
        assert (
            any_qubit is not None
        ), "Could not find any qubit in the given Circuit instance."
        circuit_to_repeat = (
            cirq.Circuit([ShiftCoordsGate(0, 0, 1).on(any_qubit)]) + circuit
        )
    repeated_circuit_operation = cirq.CircuitOperation(
        circuit_to_repeat.freeze()
    ).repeat(repetitions)
    return cirq.Circuit([repeated_circuit_operation])


class BaseLayer:
    def __init__(
        self,
        template: Template,
        plaquettes: list[Plaquette],
        top_left_corner: Position | None = None,
        repetitions: int = 1,
        add_shift_coord_gate: bool = True,
    ) -> None:
        assert repetitions >= 1 and isinstance(repetitions, numbers.Integral)

        self._template = template
        self._plaquettes = plaquettes
        self._repetitions = repetitions
        self._add_shift_coord_gate = add_shift_coord_gate
        if top_left_corner is None:
            top_left_corner = Position(0, 0)
        self._top_left_corner = top_left_corner

    def generate_circuit(self, k: int) -> cirq.Circuit:
        raw_circuit = generate_circuit(self._template.scale_to(k), self._plaquettes)
        qubit_map = {
            qubit: qubit + self._top_left_corner.to_grid_qubit()  # type: ignore
            for qubit in raw_circuit.all_qubits()
        }
        qubit_mapped_circuit = raw_circuit.transform_qubits(qubit_map)
        if self._repetitions == 1:
            return qubit_mapped_circuit
        else:
            return make_repeated_layer(
                qubit_mapped_circuit, self._repetitions, self._add_shift_coord_gate
            )

    @property
    def top_left_corner(self) -> Position:
        return self._top_left_corner

    @top_left_corner.setter
    def top_left_corner(self, new_top_left_corner: Position) -> None:
        self._top_left_corner = new_top_left_corner
