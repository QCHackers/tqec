import hashlib
from dataclasses import dataclass, field

import numpy
import numpy.typing as npt

from tqec.compile.detectors.detector import Detector
from tqec.plaquette.plaquette import Plaquettes

_NUMPY_ARRAY_HASHER = hashlib.md5


@dataclass(frozen=True)
class DetectorDatabaseKey:
    """Immutable type used as a key in the database of detectors.

    This class represents a "situation" for which we might be able to compute
    several detectors. Its purpose of existence is to provide sensible
    `__hash__` and `__eq__` operations in order to be able to use a "situation"
    as a `dict` key.

    Attributes:
        subtemplate: a 2-dimensional array of integers representing a
            sub-template.
        plaquettes_by_timestep: a list of :class:`Plaquettes`, each
            :class:`Plaquettes` entry storing enough :class:`Plaquette`
            instances to generate a circuit from `self.subtemplate` and
            corresponding to one QEC round.

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

    subtemplate: npt.NDArray[numpy.int_]
    plaquettes_by_timestep: list[Plaquettes]

    def __hash__(self) -> int:
        return hash(
            (
                self.subtemplate.shape(),
                _NUMPY_ARRAY_HASHER(self.subtemplate.tobytes()),
                tuple(self.plaquettes_by_timestep),
            )
        )

    def __eq__(self, rhs: object) -> bool:
        return (
            isinstance(rhs, DetectorDatabaseKey)
            and bool(numpy.all(self.subtemplate == rhs.subtemplate))
            and self.plaquettes_by_timestep == rhs.plaquettes_by_timestep
        )


class DetectorDatabase:
    mapping: dict[DetectorDatabaseKey, frozenset[Detector]] = field(
        default_factory=dict
    )

    def add_situation(
        self,
        subtemplate: npt.NDArray[numpy.int_],
        plaquettes_by_timestep: list[Plaquettes],
        detectors: frozenset[Detector] | Detector,
    ) -> None:
        key = DetectorDatabaseKey(subtemplate, plaquettes_by_timestep)
        self.mapping[key] = (
            frozenset([detectors]) if isinstance(detectors, Detector) else detectors
        )

    def remove_situation(
        self,
        subtemplate: npt.NDArray[numpy.int_],
        plaquettes_by_timestep: list[Plaquettes],
    ) -> None:
        key = DetectorDatabaseKey(subtemplate, plaquettes_by_timestep)
        del self.mapping[key]

    def get_detectors(
        self,
        subtemplate: npt.NDArray[numpy.int_],
        plaquettes_by_timestep: list[Plaquettes],
    ) -> frozenset[Detector] | None:
        key = DetectorDatabaseKey(subtemplate, plaquettes_by_timestep)
        return self.mapping.get(key)
