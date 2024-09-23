from __future__ import annotations

import typing as ty
from dataclasses import dataclass

import cirq
import cirq.circuits

from tqec.circuit.circuit import generate_circuit
from tqec.plaquette.plaquette import Plaquette, Plaquettes
from tqec.position import Position3D
from tqec.templates import Template
from tqec.templates.scale import LinearFunction

# NOTE: Need to change this to LinearFunction(2, -1), refer to Issue#320
_DEFAULT_BLOCK_REPETITIONS = LinearFunction(2, 1)


@dataclass
class CompiledBlock:
    template: Template
    layers: list[Plaquettes]

    @property
    def num_layers(self) -> int:
        return len(self.layers)

    def with_updated_layer(
        self,
        plaquettes_to_update: dict[int, Plaquette],
        layers_to_update: ty.Iterable[int] | None = None,
    ) -> CompiledBlock:
        if layers_to_update is None:
            layers_to_update = range(len(self.layers))
        update_layers = set(layers_to_update)
        new_plaquette_layers = []
        for i, plaquettes in enumerate(self.layers):
            if i in update_layers:
                new_plaquette_layers.append(
                    plaquettes.with_updated_plaquettes(plaquettes_to_update)
                )
            else:
                new_plaquette_layers.append(plaquettes)
        return CompiledBlock(self.template, new_plaquette_layers)

    def instantiate_layer(self, layer_index: int) -> cirq.Circuit:
        layer = self.layers[layer_index]
        return generate_circuit(self.template, layer)

    @property
    def size(self) -> int:
        template_shape = self.template.shape
        assert (
            template_shape.x == template_shape.y
        ), "Template must be square for a block."
        return 2 * template_shape.x

    def scale_to(self, k: int) -> None:
        self.template.scale_to(k)


def map_qubit_at_block(
    qubit: cirq.GridQubit,
    block_position: Position3D,
    block_size: int,
) -> cirq.GridQubit:
    return qubit + (block_position.y * block_size, block_position.x * block_size)
