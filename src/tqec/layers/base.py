import numbers
import typing as ty

import cirq
from tqec.detectors.operation import make_shift_coords
from tqec.generation.circuit import generate_circuit
from tqec.plaquette.plaquette import Plaquette
from tqec.position import Position
from tqec.templates.base import Template


def make_repeated_layer(circuit: cirq.Circuit, repetitions: int) -> cirq.Circuit:
    circuit_to_repeat = circuit + cirq.Circuit([make_shift_coords(0, 0, 1)])
    repeated_circuit_operation = cirq.CircuitOperation(
        circuit_to_repeat.freeze()
    ).repeat(repetitions)
    return cirq.Circuit([repeated_circuit_operation])


class BaseLayer:
    def __init__(
        self,
        template: Template,
        plaquettes: ty.Sequence[Plaquette],
        repetitions: int = 1,
    ) -> None:
        assert repetitions >= 1 and isinstance(repetitions, numbers.Integral)

        self._template = template
        self._plaquettes = plaquettes
        self._repetitions = repetitions

    def generate_circuit(self, k: int) -> cirq.Circuit:
        raw_circuit = generate_circuit(self._template.scale_to(k), self._plaquettes)
        shift_op_in_circuit = cirq.Circuit(cirq.Moment(make_shift_coords(0, 0, 1)))
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
