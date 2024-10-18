from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from functools import cached_property
from typing import Sequence

import numpy
import numpy.typing as npt

from tqec.circuit.generation import generate_circuit_from_instantiation
from tqec.circuit.measurement_map import MeasurementRecordsMap
from tqec.circuit.moment import Moment
from tqec.circuit.schedule import (
    Schedule,
    ScheduledCircuit,
    relabel_circuits_qubit_indices,
)
from tqec.compile.detectors.detector import Detector
from tqec.exceptions import TQECException
from tqec.plaquette.plaquette import Plaquettes
from tqec.position import Displacement
from tqec.templates.subtemplates import SubTemplateType


def _NUMPY_ARRAY_HASHER(arr: npt.NDArray[numpy.int_]) -> int:
    return int(hashlib.md5(arr.data.tobytes(), usedforsecurity=False).hexdigest(), 16)


@dataclass(frozen=True)
class _DetectorDatabaseKey:
    """Immutable type used as a key in the database of detectors.

    This class represents a "situation" for which we might be able to compute
    several detectors. Its purpose of existence is to provide sensible
    `__hash__` and `__eq__` operations in order to be able to use a "situation"
    as a `dict` key.

    Attributes:
        subtemplates: a sequence of 2-dimensional arrays of integers representing
            the sub-template(s). Each entry corresponds to one QEC round.
        plaquettes_by_timestep: a list of :class:`Plaquettes`, each
            :class:`Plaquettes` entry storing enough :class:`Plaquette`
            instances to generate a circuit from corresponding entry in
            `self.subtemplates` and corresponding to one QEC round.

    ## Implementation details

    This class uses a surjective representation to compare (`__eq__`) and hash
    (`__hash__`) its instances. This representation is computed and cached using
    the :meth:`_DetectorDatabaseKey.plaquette_names` property that basically
    uses the provided subtemplates to build a nested tuple data-structure with
    the same shape as `self.subtemplates` (3 dimensions, the first one being the
    number of time steps, the next 2 ones being of odd and equal size and
    depending on the radius used to build subtemplates) storing in each of its
    entries the corresponding plaquette name.

    This intermediate data-structure is not the most memory efficient one, but
    it has the advantage of being easy to construct, trivially invariant to
    plaquette re-indexing and easy to hash (with some care to NOT use Python's
    default `hash` due to its absence of stability across different runs).
    """

    subtemplates: Sequence[SubTemplateType]
    plaquettes_by_timestep: Sequence[Plaquettes]

    def __post_init__(self) -> None:
        if len(self.subtemplates) != len(self.plaquettes_by_timestep):
            raise TQECException(
                "DetectorDatabaseKey can only store an equal number of "
                f"subtemplates and plaquettes. Got {len(self.subtemplates)} "
                f"subtemplates and {len(self.plaquettes_by_timestep)} plaquettes."
            )

    @property
    def num_timeslices(self) -> int:
        return len(self.subtemplates)

    @cached_property
    def plaquette_names(self) -> tuple[tuple[tuple[str, ...], ...], ...]:
        return tuple(
            tuple(tuple(plaquettes[pi].name for pi in row) for row in st)
            for st, plaquettes in zip(self.subtemplates, self.plaquettes_by_timestep)
        )

    def reliable_hash(self) -> int:
        hasher = hashlib.md5()
        for timeslice in self.plaquette_names:
            for row in timeslice:
                for name in row:
                    hasher.update(name.encode())
        return int(hasher.hexdigest(), 16)

    def __hash__(self) -> int:
        return self.reliable_hash()

    def __eq__(self, rhs: object) -> bool:
        return (
            isinstance(rhs, _DetectorDatabaseKey)
            and self.plaquette_names == rhs.plaquette_names
        )

    def circuit(self, plaquette_increments: Displacement) -> ScheduledCircuit:
        """Get the `stim.Circuit` instance represented by `self`.

        Args:
            plaquette_increments: displacement between each plaquette origin.

        Returns:
            `stim.Circuit` instance represented by `self`.
        """
        circuits, qubit_map = relabel_circuits_qubit_indices(
            [
                generate_circuit_from_instantiation(
                    subtemplate, plaquettes, plaquette_increments
                )
                for subtemplate, plaquettes in zip(
                    self.subtemplates, self.plaquettes_by_timestep
                )
            ]
        )
        moments: list[Moment] = list(circuits[0].moments)
        schedule: Schedule = circuits[0].schedule
        for circuit in circuits[1:]:
            moments.extend(circuit.moments)
            schedule.append_schedule(circuit.schedule)
        return ScheduledCircuit(moments, schedule, qubit_map)


@dataclass
class DetectorDatabase:
    """Store a mapping from "situations" to the corresponding detectors.

    This class aims at storing efficiently a set of "situations" in which the
    corresponding detectors are known and do not have to be re-computed.

    In this class, a "situation" is described by :class:`DetectorDatabaseKey`
    and correspond to a spatially and temporally local piece of a larger
    computation.
    """

    mapping: dict[_DetectorDatabaseKey, frozenset[Detector]] = field(
        default_factory=dict
    )
    frozen: bool = False

    def add_situation(
        self,
        subtemplates: Sequence[SubTemplateType],
        plaquettes_by_timestep: Sequence[Plaquettes],
        detectors: frozenset[Detector] | Detector,
    ) -> None:
        """Add a new situation to the database.

        Args:
            subtemplate: a sequence of 2-dimensional arrays of integers
                representing the sub-template(s). Each entry corresponds to one
                QEC round.
            plaquettes_by_timestep: a list of :class:`Plaquettes`, each
                :class:`Plaquettes` entry storing enough :class:`Plaquette`
                instances to generate a circuit from corresponding entry in
                `self.subtemplates` and corresponding to one QEC round.
            detectors: computed detectors that should be stored in the database.
                The coordinates used by the :class:`Measurement` instances stored
                in each entry should be relative to the top-left qubit of the
                top-left plaquette in the provided `subtemplates`.

        Raises:
            TQECException: if this method is called and `self.frozen`.
        """
        if self.frozen:
            raise TQECException("Cannot add a situation to a frozen database.")
        key = _DetectorDatabaseKey(subtemplates, plaquettes_by_timestep)
        self.mapping[key] = (
            frozenset([detectors]) if isinstance(detectors, Detector) else detectors
        )

    def remove_situation(
        self,
        subtemplates: Sequence[SubTemplateType],
        plaquettes_by_timestep: Sequence[Plaquettes],
    ) -> None:
        """Remove an existing situation from the database.

        Args:
            subtemplate: a sequence of 2-dimensional arrays of integers
                representing the sub-template(s). Each entry corresponds to one
                QEC round.
            plaquettes_by_timestep: a list of :class:`Plaquettes`, each
                :class:`Plaquettes` entry storing enough :class:`Plaquette`
                instances to generate a circuit from corresponding entry in
                `self.subtemplates` and corresponding to one QEC round.

        Raises:
            TQECException: if this method is called and `self.frozen`.
        """
        if self.frozen:
            raise TQECException("Cannot remove a situation to a frozen database.")
        key = _DetectorDatabaseKey(subtemplates, plaquettes_by_timestep)
        del self.mapping[key]

    def get_detectors(
        self,
        subtemplates: Sequence[SubTemplateType],
        plaquettes_by_timestep: Sequence[Plaquettes],
    ) -> frozenset[Detector] | None:
        """Return the detectors associated with the provided situation or `None`
        if the situation is not in the database.

        Args:
            subtemplate: a sequence of 2-dimensional arrays of integers
                representing the sub-template(s). Each entry corresponds to one
                QEC round.
            plaquettes_by_timestep: a list of :class:`Plaquettes`, each
                :class:`Plaquettes` entry storing enough :class:`Plaquette`
                instances to generate a circuit from corresponding entry in
                `self.subtemplates` and corresponding to one QEC round.
            detectors: computed detectors that should be stored in the database.

        Returns:
            detectors associated with the provided situation or `None` if the
            situation is not in the database.
        """
        key = _DetectorDatabaseKey(subtemplates, plaquettes_by_timestep)
        return self.mapping.get(key)

    def freeze(self) -> None:
        self.frozen = True

    def unfreeze(self) -> None:
        self.frozen = False

    def to_crumble_urls(self, plaquette_increments: Displacement) -> list[str]:
        urls: list[str] = []
        for key, detectors in self.mapping.items():
            circuit = key.circuit(plaquette_increments)
            rec_map = MeasurementRecordsMap.from_scheduled_circuit(circuit)
            for detector in detectors:
                circuit.append_annotation(detector.to_instruction(rec_map))
            urls.append(circuit.get_circuit().to_crumble_url())
        return urls
