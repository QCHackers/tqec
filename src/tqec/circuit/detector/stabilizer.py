from dataclasses import dataclass

from tqec.circuit.detector.pauli import PauliString


@dataclass(frozen=True)
class BoundaryStabilizer:
    """Represents the state of a stabilizer on the boundary of a Fragment.

    Attributes:
        before_collapse: stabiliser before applying any collapsing operation.
        after_collapse: stabiliser after applying the collapsing operations in the
            moment.
        coords: coordinates of the stabilizer, forwarded to the detectors when
            a detector is found.
        commute_collapse_indices: TODO
        anticommute_collapse_indices: TODO
        source_measurement_indices: If this instance represents a stabilizer that has
            been propagated from a reset gate, this attribute is `None`. Else (i.e.,
            the propagation started from a measurement instruction), TODO
    """

    before_collapse: PauliString
    after_collapse: PauliString
    coords: tuple[float, ...]
    commute_collapse_indices: frozenset[int] = frozenset()
    anticommute_collapse_indices: frozenset[int] = frozenset()
    source_measurement_indices: frozenset[int] | None = None

    @property
    def all_commute(self) -> bool:
        return not bool(self.anticommute_collapse_indices)

    @property
    def is_begin_stabilizer(self) -> bool:
        return self.source_measurement_indices is not None
