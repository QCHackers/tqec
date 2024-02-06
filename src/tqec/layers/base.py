import numbers

import cirq
from tqec.detectors.gate import ShiftCoordsGate
from tqec.generation.circuit import generate_circuit
from tqec.plaquette.plaquette import Plaquette
from tqec.position import Position
from tqec.templates.base import Template


def make_repeated_layer(circuit: cirq.Circuit, repetitions: int) -> cirq.Circuit:
    circuit_to_repeat = circuit
    # Note: we do not care on which qubit it is applied, but we want a SHIFT_COORDS instruction
    #       to be inserted somewhere in the repetition loop. By convention, each timestep should
    #       ensure that the coordinates are correctly shifted for the next one, so we insert the
    #       SHIFT_COORDS at the end of the repeated circuit.
    any_qubit = next(iter(circuit.all_qubits()), None)
    assert (
        any_qubit is not None
    ), "Could not find any qubit in the given Circuit instance."
    circuit_to_repeat = circuit + cirq.Circuit([ShiftCoordsGate(0, 0, 1).on(any_qubit)])
    repeated_circuit_operation = cirq.CircuitOperation(
        circuit_to_repeat.freeze()
    ).repeat(repetitions)
    return cirq.Circuit([repeated_circuit_operation])


class BaseLayer:
    def __init__(
        self,
        template: Template,
        plaquettes: list[Plaquette],
        repetitions: int = 1,
    ) -> None:
        assert repetitions >= 1 and isinstance(repetitions, numbers.Integral)

        self._template = template
        self._plaquettes = plaquettes
        self._repetitions = repetitions

    def generate_circuit(self, k: int) -> cirq.Circuit:
        raw_circuit = generate_circuit(self._template.scale_to(k), self._plaquettes)
        # Note: we do not care on which qubit it is applied, but we want a SHIFT_COORDS instruction
        #       to be inserted at the end of the layer, because we do not want following layers to
        #       to overwrite the detectors of this layer with their own.
        any_qubit = next(iter(raw_circuit.all_qubits()), None)
        assert (
            any_qubit is not None
        ), "Could not find any qubit in the given Circuit instance."
        shift_op_in_circuit = cirq.Circuit(
            cirq.Moment(ShiftCoordsGate(0, 0, 1).on(any_qubit))
        )
        if self._repetitions == 1:
            return raw_circuit + shift_op_in_circuit
        else:
            return (
                make_repeated_layer(raw_circuit, self._repetitions)
                + shift_op_in_circuit
            )

    @property
    def top_left_corner(self) -> Position:
        return self._top_left_corner

    @top_left_corner.setter
    def top_left_corner(self, new_top_left_corner: Position) -> None:
        self._top_left_corner = new_top_left_corner
