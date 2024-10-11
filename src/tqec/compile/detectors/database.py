from dataclasses import dataclass, field
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
    return hash(arr.data.tobytes())


@dataclass(frozen=True)
class DetectorDatabaseKey:
    """Immutable type used as a key in the database of detectors.

    This class represents a "situation" for which we might be able to compute
    several detectors. Its purpose of existence is to provide sensible
    `__hash__` and `__eq__` operations in order to be able to use a "situation"
    as a `dict` key.

    Attributes:
        subtemplate: a sequence of 2-dimensional arrays of integers representing
            the sub-template(s). Each entry corresponds to one QEC round.
        plaquettes_by_timestep: a list of :class:`Plaquettes`, each
            :class:`Plaquettes` entry storing enough :class:`Plaquette`
            instances to generate a circuit from corresponding entry in
            `self.subtemplates` and corresponding to one QEC round.

    ## Implementation details

    This class stores data types that are not efficiently hashable (i.e., not in
    constant time) when considering their values:

    - `self.subtemplate` is a raw array of integers without any guarantee on the
      stored values except that they are positive.
    - `self.plaquettes_by_timestep` contains :class:`Plaquette` instances, each
      containing a class:`ScheduledCircuit` instance, ultimately containing a
      `stim.Circuit`. Hashing a quantum circuit cannot be performed in constant
      time.

    For `self.subtemplate`, we hash the `shape` of the array as well as the MD5
    hash of the array's data. This is a constant time operation, because
    we only consider spatially local detectors at the moment and that
    restriction makes sub-templates that are of constant size (w.r.t the number
    of qubits).

    For `self.plaquettes_by_timestep`, we rely on the fact that
    :class:`Plaquette` instances are immutable, which means that for each unique
    plaquette we should only have one unique instance being used in the whole
    code. This is tricky to ensure or check at the moment, and this assertion
    will have to be checked later.

    TODO: check assertion of last paragraph.
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

    def __hash__(self) -> int:
        return hash(
            (
                tuple(st.shape for st in self.subtemplates),
                tuple(_NUMPY_ARRAY_HASHER(st) for st in self.subtemplates),
                tuple(self.plaquettes_by_timestep),
            )
        )

    def __eq__(self, rhs: object) -> bool:
        return (
            isinstance(rhs, DetectorDatabaseKey)
            and len(self.subtemplates) == len(rhs.subtemplates)
            and all(
                bool(numpy.all(self_st == rhs_st))
                for self_st, rhs_st in zip(self.subtemplates, rhs.subtemplates)
            )
            and self.plaquettes_by_timestep == rhs.plaquettes_by_timestep
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

    mapping: dict[DetectorDatabaseKey, frozenset[Detector]] = field(
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
        key = DetectorDatabaseKey(subtemplates, plaquettes_by_timestep)
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
        key = DetectorDatabaseKey(subtemplates, plaquettes_by_timestep)
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
        key = DetectorDatabaseKey(subtemplates, plaquettes_by_timestep)
        return self.mapping.get(key)

    def to_crumble_urls(self, plaquette_increments: Displacement) -> list[str]:
        urls: list[str] = []
        for key, detectors in self.mapping.items():
            circuit = key.circuit(plaquette_increments)
            rec_map = MeasurementRecordsMap.from_scheduled_circuit(circuit)
            for detector in detectors:
                circuit.append_annotation(detector.to_instruction(rec_map))
            urls.append(circuit.get_circuit().to_crumble_url())
        return urls
