from __future__ import annotations

import itertools
import typing
from collections import defaultdict
from dataclasses import dataclass

from typing_extensions import override

from tqec.circuit.schedule import ScheduledCircuit
from tqec.exceptions import TQECException
from tqec.plaquette.qubit import PlaquetteQubits
from tqec.position import Position2D
from tqec.templates.scale import LinearFunction, round_or_fail
from tqec.plaquette.enums import PlaquetteOrientation


class Plaquette:
    def __init__(self, qubits: PlaquetteQubits, circuit: ScheduledCircuit) -> None:
        """Represents a QEC plaquette.

        This class stores qubits in the plaquette local coordinate system and a
        scheduled circuit that should be applied on those qubits to perform the
        QEC experiment.

        By convention, the local plaquette coordinate system is composed of a
        X-axis pointing to the right and a Y-axis pointing down.

        Args:
            qubits: qubits used by the plaquette circuit, given in the local
                plaquette coordinate system.
            circuit: scheduled quantum circuit implementing the computation that
                the plaquette should represent.

        Raises:
            TQECException: if the provided circuit uses qubits not listed in
                `qubits`.
        """
        plaquette_qubits = set(qubits)
        circuit_qubits = set(circuit.qubits)
        if not circuit_qubits.issubset(plaquette_qubits):
            wrong_qubits = circuit_qubits.difference(plaquette_qubits)
            raise TQECException(
                f"The following qubits ({wrong_qubits}) are in the provided circuit "
                "but not in the provided list of qubits."
            )
        self._qubits = qubits
        self._circuit = circuit

    @property
    def origin(self) -> Position2D:
        return Position2D(0, 0)

    @property
    def qubits(self) -> PlaquetteQubits:
        return self._qubits

    @property
    def circuit(self) -> ScheduledCircuit:
        return self._circuit

    def project_on_boundary(
        self, plaquette_orientation: PlaquetteOrientation
    ) -> Plaquette:
        """Project the plaquette on boundary and return a new plaquette with the
        remaining qubits and circuit.

        This method is useful for deriving a boundary plaquette from a integral
        plaquette.

        Args:
            plaquette_orientation: the orientation of the plaquette after the
                projection.

        Returns:
            A new plaquette with projected qubits and circuit. The qubits are
            updated to only keep the qubits on the side complementary to the
            provided orientation. The circuit is also updated to only use the
            kept qubits and empty moments with the corresponding schedules are
            removed.
        """
        kept_data_qubits = self.qubits.get_qubits_on_side(
            plaquette_orientation.to_plaquette_side()
        )
        new_plaquette_qubits = PlaquetteQubits(
            kept_data_qubits, self.qubits.syndrome_qubits
        )
        new_scheduled_circuit = self.circuit.filter_by_qubits(
            new_plaquette_qubits.all_qubits
        )
        return Plaquette(new_plaquette_qubits, new_scheduled_circuit)


CollectionType = dict[int, Plaquette] | defaultdict[int, Plaquette]


@dataclass(frozen=True)
class Plaquettes:
    """Represent a collection of plaquettes that might be applied to a
    :class:`Template` instance.

    The goal of this class is to abstract away how a "collection of plaquettes"
    is represented and to provide a unique interface in order to retrieve
    plaquettes when building a quantum circuit from a template and plaquettes.

    It also checks that the represented collection is valid, which means that it
    does not include any plaquette associated with index 0 (that is internally
    and conventionally reserved for the empty plaquette).
    """

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
