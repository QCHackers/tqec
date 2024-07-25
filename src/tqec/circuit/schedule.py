from __future__ import annotations

import numbers
import typing
from copy import deepcopy

import cirq

from tqec.circuit.operations.operation import Detector, make_detector
from tqec.exceptions import TQECException


class ScheduleException(TQECException):
    pass


class ScheduleWithNonIntegerEntriesException(ScheduleException):
    def __init__(self, schedule: list[int], non_integer_type: type) -> None:
        super().__init__(
            f"Found a non-integer entry of type {non_integer_type.__name__} in "
            f"the provided schedule {schedule}. Entries should all be integers."
        )


class ScheduleEntryTooLowException(ScheduleException):
    def __init__(self, first_schedule_entry: int, initial_virtual_moments: int) -> None:
        super().__init__(
            f"Schedule entries should be strictly greater than {ScheduledCircuit.VIRTUAL_MOMENT_SCHEDULE}. "
            f"The first schedule entry provided ({first_schedule_entry}) and the fact that "
            f"{initial_virtual_moments} virtual moments have been found before it breaks this "
            f"assumption as {first_schedule_entry} - {initial_virtual_moments} = "
            f"{first_schedule_entry - initial_virtual_moments}. Please re-number your input schedule or ask "
            "for the limit to be raised."
        )


class ScheduleCannotBeAppliedToCircuitException(ScheduleException):
    def __init__(
        self,
        circuit: cirq.Circuit,
        schedule: list[int],
        number_of_non_virtual_moments: int,
    ) -> None:
        super().__init__(
            (
                f"The provided schedule contains {len(schedule)} entries, but "
                f"{number_of_non_virtual_moments} non-virtual moments have been found in the "
                f"provided circuit:\n{circuit}"
            )
        )


class ScheduledCircuit:
    VIRTUAL_MOMENT_SCHEDULE: int = -1000

    def __init__(self, circuit: cirq.Circuit, schedule: list[int] | int = 0) -> None:
        """Represent a quantum circuit with scheduled moments.

        This class aims at representing a Circuit instance that has all its moments
        scheduled, i.e., associated with a time slice.

        Virtual moments (i.e., Moment instances that only contains Gate instances
        with the cirq.VirtualTag() tag) should not be included in the given schedule
        and will be scheduled with the special value VIRTUAL_MOMENT_SCHEDULE.

        Internally, this class only schedules the non-virtual Moment instances, but all
        its interfaces insert a schedule of VIRTUAL_MOMENT_SCHEDULE when the Moment instance
        is virtual.

        Args:
            circuit: the instance of Circuit that is scheduled.
            schedule: a sorted list of time slices indices or an integer. If a list
                is given, it should contain as many indices as there are non-virtual
                moments in the provided Circuit instance. If an integer is provided,
                each non-virtual moment of the provided Circuit is scheduled
                sequentially, starting by the provided schedule:
                `list(range(schedule, schedule + self._number_of_non_virtual_moments))`.

        Raises:
            ScheduleError: if the provided schedule is invalid.
        """
        self._is_non_virtual_moment_list: list[bool] = [
            not ScheduledCircuit._is_virtual_moment(moment)
            for moment in circuit.moments
        ]
        self._number_of_non_virtual_moments: int = sum(self._is_non_virtual_moment_list)
        if isinstance(schedule, int):
            schedule = list(
                range(schedule, schedule + self._number_of_non_virtual_moments)
            )
        else:
            ScheduledCircuit._check_input_validity(circuit, schedule)

        self._raw_circuit: cirq.Circuit = circuit
        self._schedule: list[int]
        self._set_schedule(schedule)

    @staticmethod
    def _check_input_validity(circuit: cirq.Circuit, schedule: list[int]) -> None:
        """Asserts that the given inputs are valid to construct a ScheduledCircuit instance.

        Args:
            schedule: the schedule to check.

        Raises:
            ScheduleWithNonIntegerEntries: if the given schedule has a non-integer entry.
            ScheduleNotSorted: if the given schedule is not a sorted list.
            ScheduleEntryTooLow: if the given schedule has an entry that would
                lead to incorrect scheduling.
            ScheduleCannotBeAppliedToCircuit: if the given schedule cannot be
                applied to the provided cirq.Circuit instance, for example if
                the number of entries in the schedule and the number of non-virtual moments
                in the circuit are not equal.
            TQECException: if any of the circuit qubit is not a cirq.GridQubit
                instance.
        """
        # Check that all the qubits in the cirq.Circuit instance are instances of cirq.GridQubit.
        for q in circuit.all_qubits():
            if not isinstance(q, cirq.GridQubit):
                raise TQECException(
                    f"Excepted only instances of 'cirq.GridQubit', "
                    f"but found an instance of {q.__class__.__name__}."
                )

        # Check that all entries in the provided schedule are integers.
        for entry in schedule:
            if not isinstance(entry, numbers.Integral):
                raise ScheduleWithNonIntegerEntriesException(schedule, type(entry))

        # Check that the schedule is sorted.
        is_sorted: bool = all(
            schedule[i] < schedule[i + 1] for i in range(len(schedule) - 1)
        )
        if not is_sorted:
            raise ScheduleException(
                f"The provided schedule {schedule} is not sorted. "
                "You should only provide sorted schedules."
            )

        # Ensure that ScheduledCircuit.VIRTUAL_MOMENT_SCHEDULE is the lowest possible moment schedule
        # that can be stored.
        number_of_initial_virtual_moments: int = 0
        if circuit.moments:
            while ScheduledCircuit._is_virtual_moment(
                circuit.moments[number_of_initial_virtual_moments]
            ):
                number_of_initial_virtual_moments += 1
        if (
            schedule
            and (schedule[0] - number_of_initial_virtual_moments)
            <= ScheduledCircuit.VIRTUAL_MOMENT_SCHEDULE
        ):
            raise ScheduleEntryTooLowException(
                schedule[0], number_of_initial_virtual_moments
            )

        # Ensure that the provided schedule contains as much entries as the number of non-virtual
        # moments in the circuit.
        non_virtual_moments_number: int = (
            ScheduledCircuit._compute_number_of_non_virtual_moments(circuit)
        )
        if len(schedule) != non_virtual_moments_number:
            raise ScheduleCannotBeAppliedToCircuitException(
                circuit, schedule, non_virtual_moments_number
            )

    @staticmethod
    def from_multi_qubit_moment_schedule(
        circuit: cirq.Circuit, multi_qubit_moment_schedule: list[int]
    ) -> "ScheduledCircuit":
        """Construct a ScheduledCircuit from scheduled multi-qubit gates

        This construction method basically auto-schedules single-qubit gates from
        the schedule of multi-qubit ones.

        Raises:
            ScheduleError: if the provided schedule is invalid or if the auto-
                scheduling is impossible.
        """
        ScheduledCircuit._check_input_validity(circuit, multi_qubit_moment_schedule)

        # Generate a list with all the multi-qubit moments scheduled
        number_of_non_virtual_moments = (
            ScheduledCircuit._compute_number_of_non_virtual_moments(circuit)
        )
        _NOT_SCHEDULED: int = min(multi_qubit_moment_schedule) - len(circuit.moments)
        final_schedule: list[int] = [
            _NOT_SCHEDULED for _ in range(number_of_non_virtual_moments)
        ]
        multi_qubit_moment_seen: int = 0
        for i, moment in enumerate(circuit.moments):
            # Do not check virtual moments.
            if ScheduledCircuit._is_virtual_moment(moment):
                continue
            has_multi_qubit_gate = any(len(op.qubits) > 1 for op in moment.operations)
            if has_multi_qubit_gate:
                final_schedule[i] = multi_qubit_moment_schedule[multi_qubit_moment_seen]
                multi_qubit_moment_seen += 1

        # Fill-in the single-qubit non-virtual moments schedule automatically
        # 1. fill-in the initial single-qubit moments
        first_multi_qubit_schedule = multi_qubit_moment_schedule[0]
        first_multi_qubit_moment = final_schedule.index(first_multi_qubit_schedule)
        for i, schedule in enumerate(
            range(
                first_multi_qubit_schedule - first_multi_qubit_moment,
                first_multi_qubit_schedule,
            )
        ):
            final_schedule[i] = schedule

        # 2. fill-in all the holes
        index_of_next_schedule: int = first_multi_qubit_schedule + 1
        for i in range(first_multi_qubit_moment + 1, number_of_non_virtual_moments):
            if final_schedule[i] == _NOT_SCHEDULED:
                final_schedule[i] = index_of_next_schedule
                index_of_next_schedule += 1
            else:
                index_of_next_schedule = final_schedule[i] + 1

        if _NOT_SCHEDULED in final_schedule:
            raise ScheduleException(
                f"The provided cirq.Circuit instance:\n{circuit}\n cannot be scheduled. "
                f"Final (invalid) schedule: {final_schedule}."
            )
        return ScheduledCircuit(circuit, final_schedule)

    @property
    def schedule(self) -> list[int]:
        return self._schedule

    def _set_schedule(self, new_schedule: list[int]) -> None:
        ScheduledCircuit._check_input_validity(self.raw_circuit, new_schedule)
        self._schedule = new_schedule

    @schedule.setter
    def schedule(self, new_schedule: list[int]) -> None:
        self._set_schedule(new_schedule)

    @property
    def raw_circuit(self) -> cirq.Circuit:
        return self._raw_circuit

    @raw_circuit.setter
    def raw_circuit(self, new_circuit: cirq.Circuit) -> None:
        ScheduledCircuit._check_input_validity(new_circuit, self.schedule)
        self._raw_circuit = new_circuit

    @property
    def detectors(self) -> list[Detector]:
        """Return the list of all the detectors in the circuit."""
        return [
            typing.cast(Detector, op.untagged)
            for op in self.raw_circuit.all_operations()
            if isinstance(op.untagged, Detector)
        ]

    @property
    def mappable_qubits(self) -> frozenset[cirq.GridQubit]:
        """Return the set of qubits involved in the circuit that can be mapped, which is
        the union of the qubits of all the operations performed on and the origin of all
        the detectors.
        """
        operation_qubits = self.qubits
        detector_origins = set(detector.origin for detector in self.detectors)
        return frozenset(operation_qubits.union(detector_origins))

    def map_to_qubits(
        self, qubit_map: dict[cirq.GridQubit, cirq.GridQubit], inplace: bool = False
    ) -> "ScheduledCircuit":
        """Map the qubits the ScheduledCircuit instance is applied on.

        This method forwards most of its logic to the underlying raw_circuit
        map_operations method, but additionally takes care of forwarding tags,
        changing measurements key by re-creating the correct measurements and
        re-creating Detector operation correctly.

        Args:
            qubit_map: the map used to modify the qubits.
            inplace: if True, perform the modification in place and return self.
                Else, perform the modification in a copy and return the copy.

        Returns:
            a modified instance of ScheduledCircuit (a copy if inplace is True,
            else self).
        """

        def remap_qubits(op: cirq.Operation) -> cirq.Operation:
            # See https://github.com/QCHackers/tqec/pull/127#issuecomment-1934133595
            # for an explanation on why this cast has been introduced.
            cast_qubit_map = typing.cast(dict[cirq.Qid, cirq.Qid], qubit_map)
            op = op.transform_qubits(cast_qubit_map)
            untagged = op.untagged
            if isinstance(op.gate, cirq.MeasurementGate):
                return cirq.measure(*op.qubits).with_tags(*op.tags)
            elif isinstance(untagged, Detector):
                return make_detector(
                    qubit_map.get(untagged.origin, untagged.origin),
                    untagged.relative_measurement_data,
                    time_coordinate=untagged.coordinates[-1],
                )
            else:
                return op

        operand = self if inplace else deepcopy(self)
        operand.raw_circuit = operand.raw_circuit.map_operations(remap_qubits)
        return operand

    def __copy__(self) -> "ScheduledCircuit":
        return ScheduledCircuit(
            self._raw_circuit,
            self._schedule,
        )

    def __deepcopy__(self, memo: dict) -> "ScheduledCircuit":
        return ScheduledCircuit(
            deepcopy(self._raw_circuit, memo=memo),
            deepcopy(self._schedule, memo=memo),
        )

    @property
    def scheduled_moments(self) -> typing.Iterator[tuple[cirq.Moment, int]]:
        """Yields Moment instances with their computed schedule

        This property yields all the scheduled moments. Virtual moments are scheduled
        at the timeslice ScheduledCircuit.VIRTUAL_MOMENT_SCHEDULE.

        The yielded elements are **NOT** sorted with respect to their schedule.
        Removing all the virtual elements from the yielded items, the remaining elements
        are sorted with respect to their schedule.
        """
        non_virtual_moment_index: int = 0
        for i, moment in enumerate(self.moments):
            if self._is_non_virtual_moment_list[i]:
                yield moment, self.schedule[non_virtual_moment_index]
                non_virtual_moment_index += 1
            else:
                yield moment, ScheduledCircuit.VIRTUAL_MOMENT_SCHEDULE

    @property
    def moments(self) -> typing.Iterator[cirq.Moment]:
        yield from self._raw_circuit.moments

    @property
    def qubits(self) -> frozenset[cirq.GridQubit]:
        # qubit type validation has been performed at construction
        return self._raw_circuit.all_qubits()  # type: ignore

    @property
    def number_of_non_virtual_moments(self) -> int:
        return self._number_of_non_virtual_moments

    @staticmethod
    def _is_virtual_moment(moment: cirq.Moment) -> bool:
        _virtual_tag = cirq.VirtualTag()
        return all(_virtual_tag in op.tags for op in moment.operations)

    @staticmethod
    def _compute_number_of_non_virtual_moments(circuit: cirq.Circuit) -> int:
        return sum(
            [
                not ScheduledCircuit._is_virtual_moment(moment)
                for moment in circuit.moments
            ]
        )


class ScheduledCircuits:
    def __init__(self, circuits: list[ScheduledCircuit]) -> None:
        """Represents a collection of ScheduledCircuit instances.

        This class aims at providing accessors for several instances of ScheduledCircuit.
        It allows to iterate on gates globally, for all the managed instances of
        ScheduledCircuit, and implement a few other accessor methods to help with the
        task of merging multiple ScheduledCircuit together.

        Args:
            circuits: the instances that should be managed.
        """
        self._circuits = circuits
        self._iterators = [circuit.scheduled_moments for circuit in self._circuits]
        self._current_moments = [next(it, None) for it in self._iterators]

    def has_pending_moment(self) -> bool:
        """Checks if any of the managed instances has a pending moment.

        Any moment that has not been collected by using collect_moment is considered to be pending.
        """
        return any(self._has_pending_moment(i) for i in range(len(self._circuits)))

    def _has_pending_moment(self, index: int) -> bool:
        """Check if the managed instance at the given index has a pending operation."""
        return self._current_moments[index] is not None

    def _peek_scheduled_moment(self, index: int) -> tuple[cirq.Moment, int] | None:
        """Recover **without collecting** the pending operation for the instance at the given index."""
        return self._current_moments[index]

    def _pop_scheduled_moment(self, index: int) -> tuple[cirq.Moment, int]:
        """Recover and mark as collected the pending moment for the instance at the given index.

        Raises:
            AssertionError: if not self.has_pending_operation(index).
        """
        ret = self._current_moments[index]
        if ret is None:
            raise RuntimeError(
                "Trying to pop a Moment instance from a ScheduledCircuit with all its moments already collected."
            )
        self._current_moments[index] = next(self._iterators[index], None)
        return ret

    @property
    def number_of_circuits(self) -> int:
        return len(self._circuits)

    def collect_moments(self) -> list[cirq.Moment]:
        """Collect all the moments that can be collected.

        This method collects and returns a list of all the moments that should be scheduled next.

        Due to the internal condition of ScheduledCircuit that no schedule is lower than
        ScheduledCircuit.VIRTUAL_MOMENT_SCHEDULE, virtual Moment instances are always scheduled first
        when encountered.

        Returns:
            a list of Moment instances that should be added next to the QEC
            circuit.
        """
        circuit_indices_organised_by_schedule: dict[int, list[int]] = dict()
        for circuit_index in range(self.number_of_circuits):
            if not self._has_pending_moment(circuit_index):
                continue
            _, schedule = self._peek_scheduled_moment(circuit_index)  # type: ignore
            circuit_indices_organised_by_schedule.setdefault(schedule, list()).append(
                circuit_index
            )

        if not circuit_indices_organised_by_schedule:
            return list()

        minimum_schedule = min(circuit_indices_organised_by_schedule.keys())
        moments_to_return: list[cirq.Moment] = list()
        for circuit_index in circuit_indices_organised_by_schedule[minimum_schedule]:
            moment, _ = self._pop_scheduled_moment(circuit_index)
            moments_to_return.append(moment)
        return moments_to_return


def remove_duplicate_operations(
    operations: list[cirq.Operation],
) -> list[cirq.Operation]:
    """Removes all the duplicate mergeable operations from the given list

    An instance of cirq.Operation is considered mergeable if it is tagged
    with the tag returned by Plaquette.get_mergeable_tag().
    If two operations in the provided list are considered equal **AND** are
    mergeable, this method will one of them.

    Returns:
        a list containing a copy of the cirq.Operation instances from the given
        operations, without the mergeable tag, and with mergeable duplicates
        removed from the list.
    """
    # Import needed here to resolve at runtime and avoid circular import.
    from tqec.plaquette.plaquette import Plaquette

    # Separate mergeable operations from non-mergeable ones.
    mergeable_operations: list[cirq.Operation] = list()
    final_operations: list[cirq.Operation] = list()
    for operation in operations:
        if Plaquette.get_mergeable_tag() in operation.tags:
            mergeable_operations.append(operation)
        else:
            final_operations.append(operation)
    # Remove duplicated mergeable operations with the set data-structure.
    for merged_operation in set(mergeable_operations):
        tags = set(merged_operation.tags)
        if Plaquette.get_mergeable_tag() in tags:
            tags.remove(Plaquette.get_mergeable_tag())
        final_operations.append(merged_operation.untagged.with_tags(*tags))
    return final_operations


def merge_scheduled_circuits(circuits: list[ScheduledCircuit]) -> cirq.Circuit:
    """Merge several ScheduledCircuit instances into one cirq.Circuit instance

    This function takes several scheduled circuits as input and merge them,
    respecting their schedules, into a unique cirq.Circuit instance that will
    then be returned to the caller.

    Returns:
        a circuit representing the merged scheduled circuits given as input.
    """
    scheduled_circuits = ScheduledCircuits(circuits)
    all_moments: list[cirq.Moment] = list()

    while scheduled_circuits.has_pending_moment():
        moments = scheduled_circuits.collect_moments()
        # Flatten the moments into a list of operations to perform some modifications
        operations = sum((list(moment.operations) for moment in moments), start=[])
        # Avoid duplicated operations. Any operation that have the Plaquette.get_mergeable_tag() tag
        # is considered mergeable, and can be removed if another operation in the list
        # is considered equal (and has the mergeable tag).
        non_duplicated_operations = remove_duplicate_operations(operations)
        all_moments.append(cirq.Moment(*non_duplicated_operations))

    return cirq.Circuit(all_moments)
