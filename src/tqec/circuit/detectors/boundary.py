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
        measurements: list[RelativeMeasurementLocation],
        reset_qubits: frozenset[int],
        forward: bool,
    ):
        """Represents a stabilizer that has been propagated and is now at the boundary
        of a Fragment.

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
        self._measurements = measurements
        self._collapsing_operations = collapsing_operations
        self._has_anticommuting_collapsing_operations = any(
            co.anticommutes(stabilizer) for co in collapsing_operations
        )
        self._reset_qubits: frozenset[int] = reset_qubits
        self._is_forward = forward

    @property
    def has_anticommuting_operations(self) -> bool:
        """Check if the instance represents a stabilizer that anti-commutes with at
        least one of its collapsing operations.

        Returns:
            `True` if at least one collapsing operation anti-commutes with the stabilizer,
            else `False`.
        """
        return self._has_anticommuting_collapsing_operations

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
        return self._stabilizer.collapse_by(self._collapsing_operations)

    @property
    def before_collapse(self) -> PauliString:
        """Return the stabilizer obtained before applying the collapsing operations.

        Returns:
            The Pauli string that goes out of the Fragment, before applying any
            collapsing operation.
        """
        return self._stabilizer

    @property
    def collapsing_operations(self) -> ty.Iterable[PauliString]:
        """Iterator on all the collapsing operations defining the boundary this
        stabilizer is applied to.
        """
        return self._collapsing_operations

    @property
    def measurements(self) -> list[RelativeMeasurementLocation]:
        return self._measurements

    @property
    def resets_qubits(self) -> frozenset[int]:
        return self._reset_qubits

    def merge(self, other: BoundaryStabilizer) -> BoundaryStabilizer:
        """Merge two boundary stabilizers together.

        The two merged stabilizers should be defined on the same boundaries. In particular,
        they should have the same set of collapsing operations.

        Args:
            other: the other BoundaryStabilizer to merge with self. Should have
                exactly the same set of collapsing operations.

        Raises:
            TQECException: if `self` and `other` are not defined on exactly the same
                collapsing operations.

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
        if self._is_forward != other._is_forward:
            raise TQECException(
                "Cannot merge a forward boundary stabilizer with a backward one."
            )
        is_forward_merge = self._is_forward
        stabilizer = self._stabilizer * other._stabilizer
        non_trivial_stabilizer_qubits = frozenset(stabilizer.qubits)
        # When merging 2 boundary stabilizers, particular care should be taken to merge
        # the measurements and resets.
        # The merged stabilizers might cancel out on some of the involved collapsing
        # operations, leading to collapsing operations that are in `self` and `other`
        # but that should not be in the merged result.
        # This does not happen everytime a collapsing operation is found in both
        # `self` and `other` as:
        # - merging anti-commuting stabilizer (which is the primary purpose of this
        #   method) might lead to a commuting stabilizer, still involving the collapsing
        #   operation they were previously anti-commuting with.
        # - sources (i.e., resets in forward boundary stabilizers and measurements in
        #   backward boundary operations) do not cancel each other out.
        # In the end, the end collapsing operations (resets for backward propagation,
        # measurements for forward propagation) need to be re-computed from the
        # merged stabilizer.
        reset_qubits: frozenset[int]
        measurements: list[RelativeMeasurementLocation]
        if is_forward_merge:
            reset_qubits = self.resets_qubits | other.resets_qubits
            candidate_measurements = set(self.measurements) | set(other.measurements)
            measurements = [
                m
                for m in candidate_measurements
                if m.qubit_index in non_trivial_stabilizer_qubits
            ]

        else:
            measurements = list(
                frozenset(self.measurements) | frozenset(other.measurements)
            )
            candidate_resets = self.resets_qubits | other.resets_qubits
            reset_qubits = frozenset(
                r for r in candidate_resets if r in non_trivial_stabilizer_qubits
            )
        return BoundaryStabilizer(
            stabilizer,
            self_collapsing_operations,
            measurements,
            reset_qubits,
            is_forward_merge,
        )

    def __repr__(self) -> str:
        ret = f"BoundaryStabilizers(stabilizer={self._stabilizer}, "
        ret += "collapsing_operations=["
        ret += ", ".join(str(p) for p in self.collapsing_operations)
        ret += f"], measurements={self._measurements}"
        ret += f", resets={set(self._reset_qubits)}, is_forward={self._is_forward})"
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
            qubit_coordinates[source] for source in self.source_qubits
        ]
        return tuple(numpy.mean(measurement_coordinates, axis=0))

    def with_measurement_offset(self, offset: int) -> BoundaryStabilizer:
        return BoundaryStabilizer(
            self._stabilizer,
            self.collapsing_operations,
            [m.offset_by(offset) for m in self.measurements],
            self._reset_qubits,
            self._is_forward,
        )

    def is_trivial(self) -> bool:
        return (
            not self.has_anticommuting_operations
            and self.after_collapse.non_trivial_pauli_count == 0
            and len(self._stabilizer) == 1
        )

    @property
    def source_qubits(self) -> frozenset[int]:
        return (
            self._reset_qubits
            if self._is_forward
            else frozenset(m.qubit_index for m in self.measurements)
        )


def manhattan_distance(
    lhs: BoundaryStabilizer,
    rhs: BoundaryStabilizer,
    qubit_coordinates: dict[int, tuple[float, ...]],
) -> float:
    lhs_coords = lhs.coordinates(qubit_coordinates)
    rhs_coords = rhs.coordinates(qubit_coordinates)
    return sum(abs(left - right) for left, right in zip(lhs_coords, rhs_coords))
