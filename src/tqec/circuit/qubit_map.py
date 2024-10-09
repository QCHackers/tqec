from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import Iterable

import stim

from tqec.circuit.qubit import GridQubit
from tqec.exceptions import TQECException


@dataclass(frozen=True)
class QubitMap:
    i2q: dict[int, GridQubit] = field(default_factory=dict)

    @staticmethod
    def from_qubits(qubits: Iterable[GridQubit]) -> QubitMap:
        return QubitMap(dict(enumerate(qubits)))

    @functools.cached_property
    def q2i(self) -> dict[GridQubit, int]:
        return {q: i for i, q in self.i2q.items()}

    @property
    def indices(self) -> Iterable[int]:
        return self.i2q.keys()

    @property
    def qubits(self) -> Iterable[GridQubit]:
        return self.i2q.values()

    def with_mapped_qubits(self, qubit_map: dict[GridQubit, GridQubit]) -> QubitMap:
        return QubitMap({i: qubit_map[q] for i, q in self.i2q.items()})

    def items(self) -> Iterable[tuple[int, GridQubit]]:
        return self.i2q.items()

    def filter_by_qubits(self, qubits_to_keep: Iterable[GridQubit]) -> QubitMap:
        """Filter the qubit map to only keep qubits present in the provided
        `qubits_to_keep`.

        Args:
            qubits_to_keep: the qubits to keep in the circuit.

        Returns:
            a copy of `self` for which the assertion
            `set(return_value.qubits).issubset(qubits_to_keep)` is `True`.
        """
        kept_qubits = frozenset(qubits_to_keep)
        return QubitMap({i: q for i, q in self.i2q.items() if q in kept_qubits})


def get_final_qubits(circuit: stim.Circuit) -> QubitMap:
    """Returns the existing qubits and their coordinates at the end of the
    provided `circuit`.

    Warning:
        This function, just like
        [`stim.Circuit.get_final_qubit_coordinates`](https://github.com/quantumlib/Stim/blob/main/doc/python_api_reference_vDev.md#stim.Circuit.get_final_qubit_coordinates),
        returns the qubit coordinates **at the end** of the provided `circuit`.

    Args:
        circuit: instance to get qubit coordinates from.

    Raises:
        TQECException: if any of the final qubits is not defined with exactly 2
            coordinates (we only consider qubits on a 2-dimensional grid).

    Returns:
        a mapping from qubit indices (keys) to qubit coordinates (values).
    """
    qubit_coordinates = circuit.get_final_qubit_coordinates()
    qubits: dict[int, GridQubit] = {}
    for qi, coords in qubit_coordinates.items():
        if len(coords) != 2:
            raise TQECException(
                "Qubits should be defined on exactly 2 spatial dimensions. "
                f"Found {qi} -> {coords} defined on {len(coords)} spatial dimensions."
            )
        qubits[qi] = GridQubit(*coords)
    return QubitMap(qubits)
