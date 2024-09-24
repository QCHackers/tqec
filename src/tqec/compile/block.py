from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import cirq
import cirq.circuits

from tqec.circuit.circuit import generate_circuit
from tqec.exceptions import TQECException
from tqec.plaquette.library.empty import empty_square_plaquette
from tqec.plaquette.plaquette import Plaquette, Plaquettes, RepeatedPlaquettes
from tqec.position import Position
from tqec.templates.base import RectangularTemplate
from tqec.templates.scale import LinearFunction
from tqec.templates.tiled import TiledTemplate


@dataclass
class CompiledBlock:
    """Represents a specific implementation of a cube in a `BlockGraph`.

    Attributes:
        template: the template that defines the cube implementation.
        layers: a list of `Plaquettes` that represent different functional layers of the cube.
            When aligning two `CompiledBlock`s, the layers are aligned in order. Typically, there
            are three layers in most cube implementations: Initialization, Repetitions, and Measurement.
    """

    template: RectangularTemplate
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


class TiledBlocks:
    """Represents a collection of `CompiledBlock`s tiled in a 2D grid."""

    def __init__(self, blocks_by_position: dict[Position, CompiledBlock]):
        templates_by_position: dict[Position, RectangularTemplate] = {}
        for pos, block in blocks_by_position.items():
            templates_by_position[pos] = block.template
        self._tiled_template = TiledTemplate(template_by_position=templates_by_position)
        self._tiled_layers = self._merge_layers(
            {pos: block.layers for pos, block in blocks_by_position.items()}
        )

    @property
    def block_size(self) -> int:
        return 2 * self._tiled_template.tile_shape.x

    @property
    def tiled_template(self) -> TiledTemplate:
        return self._tiled_template

    @property
    def tiled_layers(self) -> list[Plaquettes]:
        return self._tiled_layers

    def _merge_layers(
        self, layers_by_position: dict[Position, list[Plaquettes]]
    ) -> list[Plaquettes]:
        # Check if all the blocks have the same number of layers.
        num_layers = {len(layers) for layers in layers_by_position.values()}
        if len(num_layers) != 1:
            raise TQECException(
                "All blocks in the TiledBlocks should have the same number of layers."
            )
        # Check if all the block layers have the same repeating structure.
        # And merge the layers.
        indices_map = self._tiled_template.get_indices_map_for_instantiation()
        tiled_layers: list[Plaquettes] = []
        for i in range(num_layers.pop()):
            merged_plaquettes = defaultdict(empty_square_plaquette)
            repetitions: set[LinearFunction] = set()
            repeated: bool = False
            for pos, layers in layers_by_position.items():
                layer = layers[i]
                if isinstance(layer, RepeatedPlaquettes):
                    repetitions.add(layer.repetitions)
                    repeated = True
                else:
                    repetitions.add(LinearFunction(0, 0))
                if len(repetitions) > 1:
                    raise TQECException(
                        "All the block layers on the same z-plane must have the same repeating structure, i.e.",
                        "either all the layers are repeated and have the same scaling behavior for the repetitions"
                        "or none of them are repeated.",
                    )
                imap = indices_map[pos]
                merged_plaquettes.update(
                    {imap[i]: plaquette for i, plaquette in layer.collection.items()}
                )
            plaquettes = Plaquettes(merged_plaquettes)
            if repeated:
                plaquettes = plaquettes.repeat(repetitions.pop())
            tiled_layers.append(plaquettes)
        return tiled_layers

    def scale_to(self, k: int) -> None:
        """Scales all the blocks in the tiled template to the given factor."""
        self._tiled_template.scale_to(k)

    @property
    def num_layers(self) -> int:
        return len(self._tiled_layers)

    def instantiate_layer(self, layer_index: int) -> cirq.Circuit:
        """Instantiates the specified layer into a `cirq.Circuit`.

        Note that this method does not shift the circuits based on the
        tiled template. And the circuits are not repeated based on the
        repetitions in the layer.
        """
        return generate_circuit(self._tiled_template, self._tiled_layers[layer_index])
