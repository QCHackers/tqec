from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from tqec.circuit.generation import generate_circuit
from tqec.circuit.schedule import ScheduledCircuit
from tqec.exceptions import TQECException
from tqec.plaquette.library.empty import empty_square_plaquette
from tqec.plaquette.plaquette import Plaquette, Plaquettes, RepeatedPlaquettes
from tqec.position import Position2D
from tqec.scale import LinearFunction
from tqec.templates.base import RectangularTemplate
from tqec.templates.layout import LayoutTemplate


@dataclass
class CompiledBlock:
    """Represents a specific implementation of a cube in a `BlockGraph`.

    Attributes:
        template: the template that defines the cube implementation.
        layers: a list of `Plaquettes` that represent different functional layers of the
            cube. When aligning two `CompiledBlock` instances, the layers are aligned in
            order. Typically, there are three layers in most cube implementations:
            Initialization, Repetitions, and Measurement.
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


class BlockLayout:
    def __init__(self, blocks_layout: dict[Position2D, CompiledBlock]):
        """Create a layout of `CompiledBlock` instances in the 2D grid.

        We require that all the blocks in the layout have the same
        scalable shape.
        """
        template_layout: dict[Position2D, RectangularTemplate] = {}
        for pos, block in blocks_layout.items():
            template_layout[pos] = block.template
        self._template = LayoutTemplate(element_layout=template_layout)
        self._layers = self._merge_layers(
            {pos: block.layers for pos, block in blocks_layout.items()}
        )

    @property
    def template(self) -> LayoutTemplate:
        return self._template

    @property
    def layers(self) -> list[Plaquettes]:
        return self._layers

    def _merge_layers(
        self, layers_layout: dict[Position2D, list[Plaquettes]]
    ) -> list[Plaquettes]:
        """Merge the layers of the different blocks in the layout."""
        # Check if all the blocks have the same number of layers.
        num_layers = {len(layers) for layers in layers_layout.values()}
        if len(num_layers) != 1:
            raise TQECException(
                "All blocks in the layout should have the same number of layers."
            )
        # Check if all the block layers have the same repeating structure.
        # And merge the layers.
        indices_map = self._template.get_indices_map_for_instantiation()
        merged_layers: list[Plaquettes] = []
        for i in range(num_layers.pop()):
            merged_plaquettes: defaultdict[int, Plaquette] = defaultdict(
                empty_square_plaquette
            )
            repetitions: LinearFunction | None = None
            for pos, layers in layers_layout.items():
                layer = layers[i]
                if isinstance(layer, RepeatedPlaquettes):
                    if repetitions is not None and layer.repetitions != repetitions:
                        raise TQECException(
                            "All the block layers on the same z-plane must have the "
                            "same repeating structure, i.e. either all the layers are "
                            "repeated and have the same scaling behavior for the "
                            "repetitions or none of them are repeated."
                        )
                    repetitions = layer.repetitions
                imap = indices_map[pos]
                merged_plaquettes.update(
                    {imap[i]: plaquette for i, plaquette in layer.collection.items()}
                )
            plaquettes = Plaquettes(merged_plaquettes)
            if repetitions is not None:
                plaquettes = plaquettes.repeat(repetitions)
            merged_layers.append(plaquettes)
        return merged_layers

    def scale_to(self, k: int) -> None:
        """Scales all the blocks in the layout to the given factor."""
        self._template.scale_to(k)

    @property
    def num_layers(self) -> int:
        return len(self._layers)

    def instantiate_layer(self, layer_index: int) -> ScheduledCircuit:
        """Instantiates the specified layer into a `ScheduledCircuit`.

        Note that this method does not shift the circuits based on the
        layout template. And the circuits are not repeated based on the
        repetitions in the layer.
        """
        return generate_circuit(self._template, self._layers[layer_index])
