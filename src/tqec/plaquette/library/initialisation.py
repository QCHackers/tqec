from __future__ import annotations

import cirq

from tqec.circuit.schedule import ScheduledCircuit
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import (
    PlaquetteQubits,
    RoundedPlaquetteQubits,
    SquarePlaquetteQubits,
)


def z_initialisation_plaquette(qubits: PlaquetteQubits) -> Plaquette:
    circuit = cirq.Circuit(
        cirq.R(q).with_tags(Plaquette._MERGEABLE_TAG) for q in qubits.to_grid_qubit()
    )
    return Plaquette(qubits, ScheduledCircuit(circuit))


def z_initialisation_square_plaquette() -> Plaquette:
    return z_initialisation_plaquette(SquarePlaquetteQubits())


def z_initialisation_rounded_plaquette(orientation: PlaquetteOrientation) -> Plaquette:
    return z_initialisation_plaquette(RoundedPlaquetteQubits(orientation))


def x_initialisation_plaquette(qubits: PlaquetteQubits) -> Plaquette:
    circuit = cirq.Circuit(
        (cirq.R(q).with_tags(Plaquette._MERGEABLE_TAG), cirq.H(q))
        for q in qubits.to_grid_qubit()
    )
    return Plaquette(qubits, ScheduledCircuit(circuit))


def x_initialisation_square_plaquette() -> Plaquette:
    return x_initialisation_plaquette(SquarePlaquetteQubits())


def x_initialisation_rounded_plaquette(orientation: PlaquetteOrientation) -> Plaquette:
    return x_initialisation_plaquette(RoundedPlaquetteQubits(orientation))
