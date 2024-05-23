from __future__ import annotations

from enum import Enum, auto

import cirq
import stim
import stimcirq
from pydantic import BaseModel


class SupportedCircuitTypeEnum(Enum):
    cirq_json = auto()
    stim = auto()
    openqasm2 = auto()

    def parse(self, circuit: str) -> cirq.Circuit:
        if self == SupportedCircuitTypeEnum.cirq_json:
            return cirq.read_json(circuit)
        elif self == SupportedCircuitTypeEnum.stim:
            return stimcirq.stim_circuit_to_cirq_circuit(stim.Circuit(circuit))
        else:  # self == SupportedCircuitTypeEnum.openqasm2
            try:
                from cirq.contrib.qasm_import import circuit_from_qasm

                return circuit_from_qasm(circuit)
            except ImportError as e:
                raise RuntimeError(
                    "Cannot import the necessary packages to read from OpenQASM 2.0. "
                    "Have look at https://quantumai.google/cirq/build/interop#importing_from_openqasm: "
                    "you might be missing the optional `ply` package."
                ) from e

    def export(self, circuit: cirq.Circuit) -> str:
        if self == SupportedCircuitTypeEnum.cirq_json:
            return cirq.to_json(circuit)
        elif self == SupportedCircuitTypeEnum.stim:
            return stimcirq.cirq_circuit_to_stim_circuit(circuit).__str__()
        else:  # self == SupportedCircuitTypeEnum.openqasm2
            return circuit.to_qasm(header="Exporter from the TQEC package.")


class ScheduledCircuitModel(BaseModel):
    circuit_type: SupportedCircuitTypeEnum
    circuit_repr: str
    schedule: list[int]
