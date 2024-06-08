from __future__ import annotations

import typing as ty
from dataclasses import dataclass

from tqec.circuit.detectors.fragment import Fragment, FragmentLoop
from tqec.circuit.detectors.measurement import MeasurementLocation
from tqec.circuit.detectors.pauli import PauliString
from tqec.exceptions import TQECException


class BoundaryStabilizer:
    def __init__(
        self, stabilizer: PauliString, collapsing_operations: ty.Iterable[PauliString]
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
        """
        self._stabilizer = stabilizer
        self._commuting_operations: list[PauliString] = []
        self._anticommuting_operations: list[PauliString] = []
        for op in collapsing_operations:
            if stabilizer.commutes(op):
                self._commuting_operations.append(op)
            else:
                self._anticommuting_operations.append(op)

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
        return self._stabilizer.collapse_by(self._commuting_operations)

    @property
    def collapsing_operations(self) -> ty.Iterator[PauliString]:
        """Iterate on all the collapsing operations defining the boundary this
        stabilizer is applied to.
        """
        yield from self._commuting_operations
        yield from self._anticommuting_operations

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
        return BoundaryStabilizer(stabilizer, self_collapsing_operations)

    def __repr__(self) -> str:
        return (
            f"BoundaryStabilizers(stabilizer={self._stabilizer!r}, "
            f"collapsing_operations={list(self.collapsing_operations)!r})"
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
    destruction: dict[MeasurementLocation, BoundaryStabilizer]


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
    def destruction(self) -> dict[MeasurementLocation, BoundaryStabilizer]:
        return self.fragment_flows[0].destruction


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
    # First compute the flows created within the Fragment (i.e., originating from
    # reset instructions).
    creation_flows = []
    for reset_stabilizer in fragment.resets:
        final_stabilizer = reset_stabilizer.after(tableau, targets)
        touched_measurements = [
            m for m in fragment.measurements if final_stabilizer.contains(m)
        ]
        creation_flows.append(
            BoundaryStabilizer(final_stabilizer, touched_measurements)
        )

    # Then, compute the flows destructed by the Fragment (i.e., if that flow is
    # given as input, a set of measurements from the Fragment will commute with
    # the entire flow and collapse it to "no flow").
    tableau_inv = tableau.inverse()
    destruction_flows: dict[MeasurementLocation, BoundaryStabilizer] = dict()
    for measurement in fragment.measurements:
        if measurement.weight != 1:
            raise TQECException(
                "Found a measurement applied on several qubits. "
                "This is not implemented (yet?)."
            )
        (qubit,) = measurement.qubits
        measurement_location = MeasurementLocation(qubit)
        initial_stabilizer = measurement.after(tableau_inv, targets)
        touched_resets = [r for r in fragment.resets if initial_stabilizer.contains(r)]
        destruction_flows[measurement_location] = BoundaryStabilizer(
            initial_stabilizer, touched_resets
        )

    return FragmentFlows(creation=creation_flows, destruction=destruction_flows)


def _build_flows_from_fragment_loop(fragment_loop: FragmentLoop) -> FragmentLoopFlows:
    return FragmentLoopFlows(
        build_flows_from_fragments(fragment_loop.fragments), fragment_loop.repetitions
    )
