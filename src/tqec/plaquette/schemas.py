from __future__ import annotations

from pydantic import BaseModel

from tqec.circuit.schemas import ScheduledCircuitModel
from tqec.plaquette.qubit import PlaquetteQubits


class PlaquetteModel(BaseModel):
    qubits: PlaquetteQubits
    circuit: ScheduledCircuitModel


class PlaquetteLibraryModel(BaseModel):
    plaquettes: list[PlaquetteModel]
