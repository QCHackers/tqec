from __future__ import annotations

import typing as ty
from dataclasses import dataclass

import numpy
from tqec.circuit.detectors.fragment import Fragment, FragmentLoop
from tqec.circuit.detectors.match_utils.cover import (
    find_commuting_cover_on_target_qubits_sat,
)
from tqec.circuit.detectors.measurement import (
    RelativeMeasurementLocation,
    get_relative_measurement_index,
)
from tqec.circuit.detectors.pauli import PauliString, pauli_product
from tqec.exceptions import TQECException


class BoundaryStabilizer:
    def __init__(
        self,
        stabilizer: PauliString,
        collapsing_operations: ty.Iterable[PauliString],
        involved_measurements: list[RelativeMeasurementLocation],
    ):
        """Represents a stabilizer that has been propagated and is now at the boundary
        of a Fragment.

        Internally, this class separates the provided collapsing operations into
        commuting and anti-commuting collapsing operations. If there is any
        anti-commuting operation, some methods/properties will raise.

        Args:
            stabilizer: The propagated stabilizer **before** any collapsing operation
                has been applied.
            collapsing_operations: The collapsing operations the stabilizer will have to
                go through to exit the Fragment.
            involved_measurements: measurement offsets relative to the **end** of the
                fragment (even if the created BoundaryStabilizer instance represents a
                stabilizer on the beginning boundary) of measurements that are involved
                in this stabilizer.
        """
        self._stabilizer = stabilizer
        self._involved_measurements = involved_measurements
        self._commuting_operations: list[PauliString] = []
        self._anticommuting_operations: list[PauliString] = []
        for op in collapsing_operations:
            if stabilizer.commutes(op):
                self._commuting_operations.append(op)
            else:
                self._anticommuting_operations.append(op)
        self._after_collapse_cache: PauliString | None = None

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
                "Breaking pre-condition: trying two merge two BoundaryStabilizer "
                "instances that are not defined on the same boundary.\n"
                f"Collapsing operations for left-hand side: {self_collapsing_operations}.\n"
                f"Collapsing operations for right-hand side: {other_collapsing_operations}.\n"
            )
        stabilizer = self._stabilizer * other._stabilizer
        involved_measurements = list(
            set(self._involved_measurements) | set(other._involved_measurements)
        )
        return BoundaryStabilizer(
            stabilizer, self_collapsing_operations, involved_measurements
        )

    def __repr__(self) -> str:
        return (
            f"BoundaryStabilizers(stabilizer={self._stabilizer!r}, "
            f"collapsing_operations={list(self.collapsing_operations)!r}, "
            f"involved_measurements={self._involved_measurements!r})"
        )

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
        )

    def is_trivial(self) -> bool:
        return (
            not self.has_anticommuting_operations
            and self.after_collapse.weight == 0
            and len(self._stabilizer) == 1
        )


def _try_merge_anticommuting_flows_inplace(flows: list[BoundaryStabilizer]):
    # Filtering out commuting operations as they cannot make anti-commuting
    # operations commuting.
    indices_map: dict[int, int] = {}
    anticommuting_stabilizers: list[PauliString] = []
    collapsing_operations: list[set[PauliString]] = []
    for i, flow in enumerate(flows):
        if flow.has_anticommuting_operations:
            indices_map[len(indices_map)] = i
            anticommuting_stabilizers.append(flow.before_collapse)
            collapsing_operations.append(set(flow.collapsing_operations))
    # Checking a few invariants that are expected:
    # 1. all the provided flows are defined on the same boundary. This is
    #    checked by comparing the collapsing operations for each anti-commuting
    #    stabilizer and asserting that they are all equal.
    for i in range(1, len(collapsing_operations)):
        if collapsing_operations[0] != collapsing_operations[i]:
            raise TQECException(
                "Cannot merge anti-commuting flows defined on different collapsing "
                "operations. Found the following difference:\nFlow 0 has the "
                "collapsing operations:\n\t"
                + "\n\t".join(f"- {c}" for c in collapsing_operations[0])
                + f"\nFlow {i} has the collapsing operations:\n\t"
                + "\n\t".join(f"- {c}" for c in collapsing_operations[i])
                + "\n"
            )
    collapsing_pauli = pauli_product(collapsing_operations[0])
    # Now, we want to find flows in anticommuting_stabilizers that, when taken
    # into account together, commute with collapsing_pauli.
    indices_to_merge = find_commuting_cover_on_target_qubits_sat(
        collapsing_pauli, anticommuting_stabilizers
    )
    while indices_to_merge is not None:
        removed_stabilizers = [
            flows.pop(i) for i in sorted(indices_to_merge, reverse=True)
        ]
        new_commuting_stabilizer = removed_stabilizers[0]
        for removed_stabilizer in removed_stabilizers[1:]:
            new_commuting_stabilizer = new_commuting_stabilizer.merge(
                removed_stabilizer
            )
        flows.append(new_commuting_stabilizer)
        # Update for loop condition
        indices_to_merge = find_commuting_cover_on_target_qubits_sat(
            collapsing_pauli, anticommuting_stabilizers
        )


@dataclass
class FragmentFlows:
    """Stores stabilizer flows for a Fragment instance.

    Attributes:
        creation: stabilizer flows that are created by the Fragment.
            These flows originate from a single reset instruction contained
            in the Fragment.
            The measurements involved in each of these boundary stabilizers
            are the collapsing operations of the BoundaryStabilizer instances,
            so we do not need to store any measurement information alongside.
        destruction: stabilizer flows that end in the Fragment. These flows
            are generated by propagating backwards the Pauli string stabilized
            by a measurement operation contained in the Fragment.
    """

    creation: list[BoundaryStabilizer]
    destruction: list[BoundaryStabilizer]
    total_number_of_measurements: int

    @property
    def all_flows(self) -> ty.Iterator[BoundaryStabilizer]:
        yield from self.creation
        yield from self.destruction

    def remove_creation(self, index: int):
        self.creation.pop(index)

    def remove_destruction(self, index: int):
        self.destruction.pop(index)

    def remove_creations(self, indices: ty.Iterable[int]):
        for i in sorted(indices, reverse=True):
            self.remove_creation(i)

    def remove_destructions(self, indices: ty.Iterable[int]):
        for i in sorted(indices, reverse=True):
            self.remove_destruction(i)

    def without_trivial_flows(self) -> FragmentFlows:
        return FragmentFlows(
            creation=[bs for bs in self.creation if bs.is_trivial()],
            destruction=[bs for bs in self.destruction if bs.is_trivial()],
            total_number_of_measurements=self.total_number_of_measurements,
        )

    def try_merge_anticommuting_flows(self):
        _try_merge_anticommuting_flows_inplace(self.creation)
        _try_merge_anticommuting_flows_inplace(self.destruction)


@dataclass
class FragmentLoopFlows:
    """Store stabilizer flows for a FragmentLoop instance.

    This class is currently quite dumb and does not provide a sufficient
    API for generic stabilizer matching, but is enough for detectors
    that only include measurements from the current round and fron the
    previous round.
    """

    fragment_flows: list[FragmentFlows | FragmentLoopFlows]
    repeat: int

    @property
    def creation(self) -> list[BoundaryStabilizer]:
        return self.fragment_flows[-1].creation

    @property
    def destruction(self) -> list[BoundaryStabilizer]:
        return self.fragment_flows[0].destruction

    @property
    def all_flows(self) -> ty.Iterator[BoundaryStabilizer]:
        yield from self.creation
        yield from self.destruction

    @property
    def total_number_of_measurements(self) -> int:
        return sum(flow.total_number_of_measurements for flow in self.fragment_flows)

    def remove_creation(self, index: int):
        self.creation.pop(index)

    def remove_destruction(self, index: int):
        self.destruction.pop(index)

    def remove_creations(self, indices: ty.Iterable[int]):
        for i in sorted(indices, reverse=True):
            self.remove_creation(i)

    def remove_destructions(self, indices: ty.Iterable[int]):
        for i in sorted(indices, reverse=True):
            self.remove_destruction(i)

    def without_trivial_flows(self) -> FragmentLoopFlows:
        return FragmentLoopFlows(
            fragment_flows=[
                flow.without_trivial_flows() for flow in self.fragment_flows
            ],
            repeat=self.repeat,
        )

    def try_merge_anticommuting_flows(self):
        _try_merge_anticommuting_flows_inplace(self.creation)
        _try_merge_anticommuting_flows_inplace(self.destruction)


def build_flows_from_fragments(
    fragments: list[Fragment | FragmentLoop],
) -> list[FragmentFlows | FragmentLoopFlows]:
    """Compute and return the stabilizer flows of the provided fragments.

    This function ensures that the returned list will have the same "shape"
    as the input one. In more details, that means that the following property
    should be checked (recursively if there is any FragmentLoop instance in
    the provided fragments):

    ```py
    fragments: list[Fragment | FragmentLoop] = []  # anything here
    flows = build_flows_from_fragments(fragments)
    for frag, flow in zip(fragments, flows):
        assert (isinstance(frag, Fragment) and isinstance(flow, FragmentFlow)) or (
            isinstance(frag, FragmentLoop) and isinstance(flow, FragmentLoopFlow)
        )
    ```

    Args:
        fragments: the fragments composing the circuit to study and for which this
            function should compute flows.

    Returns:
        the computed flows for each of the provided fragments.
    """
    return [
        _build_flows_from_fragment(fragment)
        if isinstance(fragment, Fragment)
        else _build_flows_from_fragment_loop(fragment)
        for fragment in fragments
    ]


def _build_flows_from_fragment(fragment: Fragment) -> FragmentFlows:
    tableau = fragment.get_tableau()
    targets = list(range(len(tableau)))
    sorted_qubit_involved_in_measurements = fragment.measurements_qubits

    # First compute the flows created within the Fragment (i.e., originating from
    # reset instructions).
    creation_flows: list[BoundaryStabilizer] = []
    for reset_stabilizer in fragment.resets:
        final_stabilizer = reset_stabilizer.after(tableau, targets)
        involved_measurements = [
            m for m in fragment.measurements if final_stabilizer.overlaps(m)
        ]
        involved_measurements_offsets = [
            get_relative_measurement_index(
                sorted_qubit_involved_in_measurements, m.qubit
            )
            for m in involved_measurements
        ]

        creation_flows.append(
            BoundaryStabilizer(
                final_stabilizer, involved_measurements, involved_measurements_offsets
            )
        )

    # Then, compute the flows destructed by the Fragment (i.e., if that flow is
    # given as input, a set of measurements from the Fragment will commute with
    # the entire flow and collapse it to "no flow").
    tableau_inv = tableau.inverse()
    destruction_flows: list[BoundaryStabilizer] = []
    for measurement in fragment.measurements:
        if measurement.weight != 1:
            raise TQECException(
                "Found a measurement applied on several qubits. "
                "This is not implemented (yet?)."
            )
        (qubit,) = measurement.qubits

        initial_stabilizer = measurement.after(tableau_inv, targets)
        touched_resets = [r for r in fragment.resets if initial_stabilizer.contains(r)]
        destruction_flows.append(
            BoundaryStabilizer(
                initial_stabilizer,
                touched_resets,
                [
                    get_relative_measurement_index(
                        sorted_qubit_involved_in_measurements, qubit
                    )
                ],
            ),
        )

    return FragmentFlows(
        creation=creation_flows,
        destruction=destruction_flows,
        total_number_of_measurements=len(fragment.measurements),
    )


def _build_flows_from_fragment_loop(fragment_loop: FragmentLoop) -> FragmentLoopFlows:
    return FragmentLoopFlows(
        build_flows_from_fragments(fragment_loop.fragments), fragment_loop.repetitions
    )
