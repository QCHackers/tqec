from __future__ import annotations

import itertools
import typing
from collections import defaultdict
from dataclasses import dataclass

from tqec.circuit.operations.measurement import (
    Measurement,
    get_measurements_from_circuit,
)
from tqec.circuit.schedule import ScheduledCircuit
from tqec.exceptions import TQECException
from tqec.plaquette.qubit import PlaquetteQubits
from tqec.position import Position


class Plaquette:
    _MERGEABLE_TAG: str = "tqec_can_be_merged"

    @staticmethod
    def get_mergeable_tag() -> str:
        return Plaquette._MERGEABLE_TAG

    def __init__(
        self,
        qubits: PlaquetteQubits,
        circuit: ScheduledCircuit,
    ) -> None:
        """Represents a QEC plaquette.

        This class stores qubits in the plaquette local coordinate system and a scheduled
        circuit that should be applied on those qubits to perform the QEC experiment.

        By convention, the local plaquette coordinate system is composed of a X-axis pointing
        to the right and a Y-axis pointing down.

        Args:
            qubits: qubits used by the plaquette circuit, given in the local
                plaquette coordinate system.
            circuit: scheduled quantum circuit implementing the computation that
                the plaquette should represent.

        Raises:
            TQECException: if the provided circuit uses qubits not in the list of
                PlaquetteQubit.
        """
        plaquette_qubits = {qubit.to_grid_qubit() for qubit in qubits}
        circuit_qubits = set(circuit.raw_circuit.all_qubits())
        if not circuit_qubits.issubset(plaquette_qubits):
            wrong_qubits = circuit_qubits.difference(plaquette_qubits)
            raise TQECException(
                f"The following qubits ({wrong_qubits}) are in the provided circuit "
                "but not in the list of PlaquetteQubit."
            )
        self._qubits = qubits
        self._circuit = circuit
        self._measurements = get_measurements_from_circuit(circuit.raw_circuit)

    @property
    def origin(self) -> Position:
        return Position(0, 0)

    @property
    def qubits(self) -> PlaquetteQubits:
        return self._qubits

    @property
    def circuit(self) -> ScheduledCircuit:
        return self._circuit

    @property
    def measurements(self) -> list[Measurement]:
        return self._measurements


def _to_plaquette_dict(
    plaquettes: list[Plaquette] | dict[int, Plaquette] | defaultdict[int, Plaquette],
) -> dict[int, Plaquette] | defaultdict[int, Plaquette]:
    if isinstance(plaquettes, (dict, defaultdict)):
        return plaquettes
    return {i: p for i, p in enumerate(plaquettes)}


@dataclass(frozen=True)
class Plaquettes:
    collection: list[Plaquette] | dict[int, Plaquette] | defaultdict[int, Plaquette]

    def __post_init__(self) -> None:
        if not isinstance(self.collection, (list, dict, defaultdict)):
            raise TQECException(
                f"Plaquettes initialized with {type(self.collection)} but only list, "
                "dict and defaultdict instances are allowed."
            )

    def __getitem__(self, index: int) -> Plaquette:
        return self.collection[index]

    def __iter__(self) -> typing.Iterator[Plaquette]:
        if isinstance(self.collection, list):
            return iter(self.collection)
        if isinstance(self.collection, defaultdict):
            if self.collection.default_factory is not None:
                default = self.collection.default_factory()
                return itertools.chain(
                    self.collection.values(), [default] if default is not None else []
                )
            else:
                return iter(self.collection.values())
        if isinstance(self.collection, dict):
            return iter(self.collection.values())
        else:
            raise TQECException(
                f"Plaquette is initialised with the wrong type: {type(self.collection)}."
            )

    @property
    def has_default(self) -> bool:
        return isinstance(self.collection, defaultdict)

    def __len__(self) -> int:
        if isinstance(self.collection, defaultdict):
            raise TQECException(
                "Cannot accurately get the length of a defaultdict instance."
            )
        return len(self.collection)

    def __or__(self, other: Plaquettes | dict[int, Plaquette]) -> Plaquettes:
        other_plaquettes = (
            _to_plaquette_dict(other.collection)
            if isinstance(other, Plaquettes)
            else other
        )
        return Plaquettes(_to_plaquette_dict(self.collection) | other_plaquettes)
