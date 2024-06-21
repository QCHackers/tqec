from __future__ import annotations

import typing as ty

import numpy
from tqec.circuit.detectors.measurement import RelativeMeasurementLocation
from tqec.circuit.detectors.pauli import PauliString
from tqec.exceptions import TQECException


class BoundaryStabilizer:
    def __init__(
        self,
        stabilizer: PauliString,
        collapsing_operations: ty.Iterable[PauliString],
        involved_measurements: list[RelativeMeasurementLocation],
        source_qubits: frozenset[int],
    ):
        """Represents a stabilizer that has been propagated and is now at the boundary
        of a Fragment.

        Internally, this class separates the provided collapsing operations into
        commuting and anti-commuting collapsing operations. If there is any
        anti-commuting operation, some methods/properties will raise an exception.

        Raises:
            TQECException: if `source_qubits` is empty.

        Args:
            stabilizer: The propagated stabilizer **before** any collapsing operation
                has been applied.
            collapsing_operations: The collapsing operations the stabilizer will have to
                go through to exit the Fragment.
            involved_measurements: measurement offsets relative to the **end** of the
                fragment (even if the created BoundaryStabilizer instance represents a
                stabilizer on the beginning boundary) of measurements that are involved
                in this stabilizer.
            source_qubit: index of the qubit on which the collapsing operation that started
                the propagation of this boundary stabilizer was applied on.
                Should contain at least one index.
        """
        self._stabilizer = stabilizer
        self._involved_measurements = involved_measurements
        self._commuting_operations: list[PauliString] = []
        self._anticommuting_operations: list[PauliString] = []
        for op in set(collapsing_operations):
            if stabilizer.commutes(op):
                self._commuting_operations.append(op)
            else:
                self._anticommuting_operations.append(op)
        self._after_collapse_cache: PauliString | None = None
        if not source_qubits:
            raise TQECException(
                "Cannot define a BoundaryStabilizer without at least one source qubit."
            )
        self._source_qubits: frozenset[int] = source_qubits

    @property
    def has_anticommuting_operations(self) -> bool:
        """Check if the instance represents a stabilizer that anti-commutes with at
        least one of its collapsing operations.

        Returns:
            `True` if at least one collapsing operation anti-commutes with the stabilizer,
            else `False`.
        """
        return bool(self._anticommuting_operations)

    @property
    def after_collapse(self) -> PauliString:
        """Compute the stabilizer obtained after applying the collapsing operations.

        Raises:
            TQECException: If any of the collapsing operation anti-commutes with the
                stored stabilizer.

        Returns:
            The collapsed Pauli string that goes out of the Fragment.
        """
        if self.has_anticommuting_operations:
            raise TQECException(
                "Cannot collapse a BoundaryStabilizer if it has "
                "anticommuting operations."
            )
        if self._after_collapse_cache is None:
            self._after_collapse_cache = self._stabilizer.collapse_by(
                self._commuting_operations
            )
        return self._after_collapse_cache

    @property
    def before_collapse(self) -> PauliString:
        """Return the stabilizer obtained before applying the collapsing operations.

        Returns:
            The Pauli string that goes out of the Fragment, before applying any
            collapsing operation.
        """
        return self._stabilizer

    @property
    def collapsing_operations(self) -> ty.Iterator[PauliString]:
        """Iterate on all the collapsing operations defining the boundary this
        stabilizer is applied to.
        """
        yield from self._commuting_operations
        yield from self._anticommuting_operations

    @property
    def involved_measurements(self) -> list[RelativeMeasurementLocation]:
        return self._involved_measurements

    def merge(self, other: BoundaryStabilizer) -> BoundaryStabilizer:
        """Merge two boundary stabilizers together.

        The two merged stabilizers should be defined on the same boundaries. In particular,
        they should have the same set of collapsing operations.

        Args:
            other: the other BoundaryStabilizer to merge with self. Should have
                exactly the same set of collapsing operations.

        Returns:
            the merged boudary stabilizer, defined on the same set of collapsing
            operations (i.e., the same boundary), but with the two pre-collapsing
            stabilizers multiplied together.
        """
        self_collapsing_operations = set(self.collapsing_operations)
        other_collapsing_operations = set(other.collapsing_operations)
        if self_collapsing_operations != other_collapsing_operations:
            raise TQECException(
                "Breaking pre-condition: trying to merge two BoundaryStabilizer "
                "instances that are not defined on the same boundary.\n"
                f"Collapsing operations for left-hand side: {self_collapsing_operations}.\n"
                f"Collapsing operations for right-hand side: {other_collapsing_operations}.\n"
            )
        stabilizer = self._stabilizer * other._stabilizer
        involved_measurements = list(
            set(self._involved_measurements) | set(other._involved_measurements)
        )
        source_qubits = self._source_qubits | other._source_qubits
        return BoundaryStabilizer(
            stabilizer, self_collapsing_operations, involved_measurements, source_qubits
        )

    def __repr__(self) -> str:
        ret = f"BoundaryStabilizers(stabilizer={self._stabilizer}, "
        ret += "collapsing_operations=["
        ret += ", ".join(str(p) for p in self.collapsing_operations)
        ret += f"], involved_measurements={self._involved_measurements})"
        return ret

    def coordinates(
        self, qubit_coordinates: dict[int, tuple[float, ...]]
    ) -> tuple[float, ...]:
        """Compute and return the coordinates of the boundary stabilizer.

        The coordinates of a given boundary stabilizer is defined as the average of
        the coordinates of each collapsing operations it represents.

        Args:
            qubit_coordinates: mapping from qubit indices to coordinates

        Returns:
            the boundary stabilizer coordinates.
        """
        measurement_coordinates = [
            qubit_coordinates[measurement.qubit_index]
            for measurement in self.involved_measurements
        ]
        return tuple(numpy.mean(measurement_coordinates, axis=0))

    def with_measurement_offset(self, offset: int) -> BoundaryStabilizer:
        return BoundaryStabilizer(
            self._stabilizer,
            self.collapsing_operations,
            [m.offset_by(offset) for m in self.involved_measurements],
            self._source_qubits,
        )

    def is_trivial(self) -> bool:
        return (
            not self.has_anticommuting_operations
            and self.after_collapse.non_trivial_pauli_count == 0
            and len(self._stabilizer) == 1
        )


def manhattan_distance(
    lhs: BoundaryStabilizer,
    rhs: BoundaryStabilizer,
    qubit_coordinates: dict[int, tuple[float, ...]],
) -> float:
    lhs_coords = lhs.coordinates(qubit_coordinates)
    rhs_coords = rhs.coordinates(qubit_coordinates)
    return sum(abs(left - right) for left, right in zip(lhs_coords, rhs_coords))
