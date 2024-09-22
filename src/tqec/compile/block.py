from __future__ import annotations

import typing as ty
from dataclasses import dataclass

import cirq
import cirq.circuits

from tqec.circuit.circuit import generate_circuit
from tqec.circuit.operations.measurement import Measurement, RepeatedMeasurement
from tqec.circuit.schedule import ScheduledCircuit, merge_scheduled_circuits
from tqec.exceptions import TQECException
from tqec.plaquette.plaquette import Plaquette, Plaquettes, RepeatedPlaquettes
from tqec.position import Position3D
from tqec.templates import Template
from tqec.templates.interval import Interval
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

    @property
    def first_layer(self) -> Plaquettes:
        return self.layers[0]

    @property
    def last_layer(self) -> Plaquettes:
        return self.layers[-1]

    def with_updated_plaquettes(
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

    @property
    def depth(self) -> int:
        """Return the number of `cirq.Moment` needed to execute all the
        plaquettes."""
        depth = 0
        for layer in self.layers:
            t = max(max(p.circuit.schedule, default=0) for p in layer)
            if isinstance(layer, RepeatedPlaquettes):
                t *= layer.num_rounds(self.template.k)
            depth += t
        return depth

    def instantiate_layer(self, layer_index: int) -> cirq.Circuit:
        layer = self.layers[layer_index]
        return generate_circuit(self.template, layer.collection)

    def scale_to(self, k: int) -> None:
        self.template.scale_to(k)

    # @staticmethod
    # def _get_measurements(
    #     template: Template, plaquettes: Plaquettes
    # ) -> ty.Iterator[Measurement]:
    #     template_array = template.instantiate()
    #     default_increments = template.get_increments()
    #
    #     for i, row in enumerate(template_array):
    #         for j, plaquette_index in enumerate(row):
    #             xoffset = j * default_increments.x
    #             yoffset = i * default_increments.y
    #             yield from (
    #                 m.offset_spatially_by(xoffset, yoffset)
    #                 for m in plaquettes[plaquette_index].measurements
    #             )
    #
    # @property
    # def measurements(self) -> frozenset[Measurement | RepeatedMeasurement]:
    #     """Returns all the measurements in the block, relative to the end of
    #     the block."""
    #     measurement_number_by_qubits: dict[cirq.GridQubit, int] = {}
    #     all_measurements: list[Measurement | RepeatedMeasurement] = []
    #     # Start by the final measurements.
    #     for final_measurement in self._get_measurements(
    #         self.template, self.final_plaquettes
    #     ):
    #         all_measurements.append(final_measurement)
    #         measurement_number_by_qubits[final_measurement.qubit] = 1
    #     # Continue with the repeating measurements
    #     if self.repeating_plaquettes is not None:
    #         repetitions = self.repeating_plaquettes.number_of_rounds(self.template.k)
    #         for repeating_measurement in self._get_measurements(
    #             self.template, self.repeating_plaquettes.plaquettes
    #         ):
    #             qubit = repeating_measurement.qubit
    #             past_measurement_number = measurement_number_by_qubits.get(qubit, 0)
    #             all_measurements.append(
    #                 RepeatedMeasurement(
    #                     qubit,
    #                     Interval(
    #                         -past_measurement_number - repetitions,
    #                         -past_measurement_number,
    #                         start_excluded=False,
    #                         end_excluded=True,
    #                     ),
    #                 )
    #             )
    #             measurement_number_by_qubits[repeating_measurement.qubit] = (
    #                 past_measurement_number + repetitions
    #             )
    #     # Finish with the initial measurements
    #     for initial_measurement in self._get_measurements(
    #         self.template, self.initial_plaquettes
    #     ):
    #         qubit = repeating_measurement.qubit
    #         past_measurement_number = measurement_number_by_qubits.get(qubit, 0)
    #         all_measurements.append(
    #             initial_measurement.offset_temporally_by(-past_measurement_number)
    #         )
    #
    #     return frozenset(all_measurements)
    #
    # @property
    # def all_measurements(self) -> list[Measurement]:
    #     measurements: list[Measurement] = []
    #     for m in self.measurements:
    #         if isinstance(m, Measurement):
    #             measurements.append(m)
    #         else:  # isinstance(m, RepeatedMeasurement):
    #             measurements.extend(m.measurements())
    #     return measurements
