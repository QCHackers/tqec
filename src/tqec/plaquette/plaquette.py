from __future__ import annotations

import typing
from typing_extensions import override
import itertools
from collections import defaultdict
from dataclasses import dataclass

from tqec.circuit.operations.measurement import (
    Measurement,
    get_measurements_from_circuit,
)
from tqec.circuit.schedule import ScheduledCircuit
from tqec.exceptions import TQECException
from tqec.plaquette.qubit import PlaquetteQubits
from tqec.position import Position2D
from tqec.templates.scale import LinearFunction, round_or_fail


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
    def origin(self) -> Position2D:
        return Position2D(0, 0)

    @property
    def qubits(self) -> PlaquetteQubits:
        return self._qubits

    @property
    def circuit(self) -> ScheduledCircuit:
        return self._circuit

    def with_circuit(self, circuit: ScheduledCircuit) -> Plaquette:
        return Plaquette(self.qubits, circuit)

    @property
    def measurements(self) -> list[Measurement]:
        return self._measurements


CollectionType = dict[int, Plaquette] | defaultdict[int, Plaquette]


@dataclass(frozen=True)
class Plaquettes:
    collection: CollectionType

    def __post_init__(self) -> None:
        if not isinstance(self.collection, (dict, defaultdict)):
            raise TQECException(
                f"Plaquettes initialized with {type(self.collection)} but only"
                "dict and defaultdict instances are allowed."
            )
        if 0 in self.collection:
            raise TQECException(
                "Found a Plaquette with index 0. This index is reserved to express "
                '"no plaquette". Please re-number your plaquettes starting from 1.'
            )

    def __getitem__(self, index: int) -> Plaquette:
        return self.collection[index]

    def __iter__(self) -> typing.Iterator[Plaquette]:
        if (
            isinstance(self.collection, defaultdict)
            and self.collection.default_factory is not None
        ):
            default = self.collection.default_factory()
            return itertools.chain(
                self.collection.values(), [default] if default is not None else []
            )
        return iter(self.collection.values())

    @property
    def has_default(self) -> bool:
        return isinstance(self.collection, defaultdict)

    def __len__(self) -> int:
        if isinstance(self.collection, defaultdict):
            raise TQECException(
                "Cannot accurately get the length of a defaultdict instance."
            )
        return len(self.collection)

    def repeat(self, repetitions: LinearFunction) -> RepeatedPlaquettes:
        return RepeatedPlaquettes(self.collection, repetitions)

    def with_updated_plaquettes(
        self, plaquettes_to_update: dict[int, Plaquette]
    ) -> Plaquettes:
        return Plaquettes(self.collection | plaquettes_to_update)


@dataclass(frozen=True)
class RepeatedPlaquettes(Plaquettes):
    """Represent plaquettes that should be repeated for several rounds."""

    repetitions: LinearFunction

    def num_rounds(self, k: int) -> int:
        return round_or_fail(self.repetitions(k))

    @override
    def with_updated_plaquettes(
        self, plaquettes_to_update: dict[int, Plaquette]
    ) -> RepeatedPlaquettes:
        return RepeatedPlaquettes(
            self.collection | plaquettes_to_update,
            repetitions=self.repetitions,
        )
