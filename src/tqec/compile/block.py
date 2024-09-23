from __future__ import annotations

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
    """Represents a specific implementation of a cube in a `BlockGraph`.

    Attributes:
        template: the template that defines the cube implementation.
        layers: a list of `Plaquettes` that represent different functional layers of the cube.
            When aligning two `CompiledBlock`s, the layers are aligned in order. Typically, there
            are three layers in most cube implementations: Initialization, Repetitions, and Measurement.
    """

    template: Template
    layers: list[Plaquettes]

    @property
    def num_layers(self) -> int:
        return len(self.layers)

    def with_updated_layer(
        self,
        plaquettes_to_update: dict[int, Plaquette],
        layer_to_update: int,
    ) -> CompiledBlock:
        """Returns a new `CompiledBlock` with the specified layer updated.

        Args:
            plaquettes_to_update: a dictionary of plaquettes to update in the layer.
            layer_to_update: the index of the layer to update.
        """
        new_plaquette_layers = []
        for i, plaquettes in enumerate(self.layers):
            if i == layer_to_update:
                new_plaquette_layers.append(
                    plaquettes.with_updated_plaquettes(plaquettes_to_update)
                )
            else:
                new_plaquette_layers.append(plaquettes)
        return CompiledBlock(self.template, new_plaquette_layers)

    def instantiate_layer(self, layer_index: int) -> cirq.Circuit:
        """Instantiates the specified layer into a `cirq.Circuit`."""
        layer = self.layers[layer_index]
        return generate_circuit(self.template, layer)

    @property
    def size(self) -> int:
        """Returns the spatial width/height of the block.

        The block is assumed to be square, so the width and height are
        the same.
        """
        template_shape = self.template.shape
        assert (
            template_shape.x == template_shape.y
        ), "Template must be square for a block."
        return 2 * template_shape.x

    def scale_to(self, k: int) -> None:
        """Scales the underlying template in space and implicitly the repeated
        layers in time direction."""
        self.template.scale_to(k)


def map_qubit_at_block(
    qubit: cirq.GridQubit,
    block_position: Position3D,
    block_size: int,
) -> cirq.GridQubit:
    """Map a qubit in the block to the global qubit position."""
    return qubit + (block_position.y * block_size, block_position.x * block_size)
