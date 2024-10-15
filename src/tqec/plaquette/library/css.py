"""Define the standard CSS-type surface code plaquettes."""

from __future__ import annotations

from typing import Literal

import stim

from tqec.circuit.qubit_map import QubitMap
from tqec.circuit.schedule import ScheduledCircuit
from tqec.circuit.moment import Moment, iter_stim_circuit_without_repeat_by_moments
from tqec.plaquette.enums import MeasurementBasis, PlaquetteSide, ResetBasis
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import SquarePlaquetteQubits


def make_css_surface_code_plaquette(
    basis: Literal["X", "Z"],
    data_initialization: ResetBasis | None = None,
    data_measurement: MeasurementBasis | None = None,
    x_boundary_orientation: Literal["HORIZONTAL", "VERTICAL"] = "VERTICAL",
    init_meas_only_on_side: PlaquetteSide | None = None,
) -> Plaquette:
    """Make a CSS-type surface code plaquette.

    Args:
        basis: the basis of the plaquette.
        x_boundary_orientation: the orientation of the X boundary.
        data_initialization: the logical basis for data initialization.
        data_measurement: the logical basis for data measurement.
        init_meas_only_on_side: the side for data initialization and measurement.

    Returns:
        A CSS-type surface code plaquette.
    """
    builder = _CSSPlaquetteBuilder(basis, x_boundary_orientation)
    if data_initialization is not None:
        builder.add_data_init_or_meas(data_initialization, init_meas_only_on_side)
    if data_measurement is not None:
        builder.add_data_init_or_meas(data_measurement, init_meas_only_on_side)
    return builder.build()


class _CSSPlaquetteBuilder:
    MERGEABLE_INSTRUCTIONS = frozenset(("M", "MZ", "MX", "R", "RZ", "RX"))

    def __init__(
        self,
        basis: Literal["X", "Z"],
        x_boundary_orientation: Literal["HORIZONTAL", "VERTICAL"],
    ) -> None:
        self._basis = basis
        self._x_boundary_orientation = x_boundary_orientation
        self._moments: list[Moment] = self._build_memory_moments()
        self._qubits = SquarePlaquetteQubits()
        self._qubit_map = QubitMap(
            {0: self._qubits.syndrome_qubits[0]}
            | {i + 1: q for i, q in enumerate(self._qubits.data_qubits)}
        )

    def build(self) -> Plaquette:
        return Plaquette(
            self._qubits,
            ScheduledCircuit(
                self._moments,
                schedule=list(range(len(self._moments))),
                qubit_map=self._qubit_map,
            ),
            mergeable_instructions=self.MERGEABLE_INSTRUCTIONS,
        )

    def add_data_init_or_meas(
        self,
        basis: ResetBasis | MeasurementBasis,
        only_on_side: PlaquetteSide | None = None,
    ) -> None:
        moment_index = 0 if isinstance(basis, ResetBasis) else -1
        self._moments[moment_index].append(
            f"{basis.instruction_name}", self._get_data_qubits(only_on_side), []
        )

    def _build_memory_moments(self) -> list[Moment]:
        circuit = stim.Circuit()
        circuit.append(f"R{self._basis}", [0], [])
        circuit.append("TICK", [], [])

        # adjust cnot order to make the hook errors perpendicular to the boundary
        match self._basis, self._x_boundary_orientation:
            case ("X", "HORIZONTAL") | ("Z", "VERTICAL"):
                cnot_order = [1, 2, 3, 4]
            case _:
                cnot_order = [1, 3, 2, 4]
        for dq in cnot_order:
            circuit.append("CX", [0, dq][:: (-1 if self._basis == "Z" else 1)], [])
            circuit.append("TICK", [], [])

        circuit.append(f"M{self._basis}", [0], [])
        return list(iter_stim_circuit_without_repeat_by_moments(circuit))

    def _get_data_qubits(self, only_on_side: PlaquetteSide | None = None) -> list[int]:
        if only_on_side is None:
            return [1, 2, 3, 4]
        target_qubits = self._qubits.get_qubits_on_side(only_on_side)
        return sorted(self._qubit_map.q2i[q] for q in target_qubits)
