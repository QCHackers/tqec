import typing
from copy import deepcopy

import cirq

from tqec.detectors.gate import DetectorGate


class ScheduledCircuit:
    VIRTUAL_MOMENT_SCHEDULE: int = -1000

    def __init__(
        self, circuit: cirq.Circuit, schedule: list[int] | None = None
    ) -> None:
        """Represent a quantum circuit with scheduled moments.

        This class aims at representing a Circuit instance that has all its moments
        scheduled, i.e., associated with a time slice.

        Virtual moments (i.e., Moment instances that only contains Gate instances
        with the cirq.VirtualTag() tag) should not be included in the given schedule
        and will be scheduled with the special value VIRTUAL_MOMENT_SCHEDULE.

        Internally, this class only schedules the non-virtual Moment instances, but all
        its interfaces insert a schedule of VIRTUAL_MOMENT_SCHEDULE when the Moment instance
        is virtual.

        :param circuit: the instance of Circuit that is scheduled.
        :param schedule: a sorted list of time slices indices. The list should contain
            as much indices as there are non-virtual moments in the provided Circuit
            instance. If the list is None, it default to
            `list(range(number_of_non_virtual_moments))`.

        :raises AssertionError: if the provided schedule is invalid.
        """
        self._is_non_virtual_moment_list: list[bool] = [
            not ScheduledCircuit._is_virtual_moment(moment)
            for moment in circuit.moments
        ]
        self._number_of_non_virtual_moments: int = sum(self._is_non_virtual_moment_list)
        if schedule is None:
            schedule = list(range(self._number_of_non_virtual_moments))
        else:
            ScheduledCircuit._check_input_schedule_validity(schedule)
            assert len(schedule) == self._number_of_non_virtual_moments, (
                f"Cannot create a ScheduledCircuit instance with a different number "
                f"of non-virtual moments ({self._number_of_non_virtual_moments}) and time slices "
                f"in the provided schedule ({len(schedule)})."
            )
        self._raw_circuit: cirq.Circuit = circuit
        self._schedule: list[int]
        self.schedule = schedule

    @staticmethod
    def _check_input_schedule_validity(schedule: list[int]) -> None:
        """Asserts that the given schedule is valid

        A valid input schedule is composed on entries that are:
        1. sorted
        2. unique
        3. all strictly greater than ScheduledCircuit.VIRTUAL_MOMENT_SCHEDULE

        This static method checks the above points by using asserts.

        :param schedule: the schedule to check.
        :raises AssertionError: if the given schedule is invalid.
        """
        assert all(
            schedule[i] < schedule[i + 1] for i in range(len(schedule) - 1)
        ), "Given schedule should be a sorted list of unique integers."
        # Ensure that ScheduledCircuit._VIRTUAL_MOMENT_SCHEDULE is the lowest possible moment schedule
        # that can be stored.
        assert (
            len(schedule) == 0 or schedule[0] > ScheduledCircuit.VIRTUAL_MOMENT_SCHEDULE
        ), f"Moment schedules cannot be lower than {ScheduledCircuit.VIRTUAL_MOMENT_SCHEDULE}. Found {schedule[0]}."

    @staticmethod
    def from_multi_qubit_moment_schedule(
        circuit: cirq.Circuit, multi_qubit_moment_schedule: list[int]
    ) -> "ScheduledCircuit":
        """Construct a ScheduledCircuit from scheduled multi-qubit gates

        This construction method basically auto-schedules single-qubit gates from
        the schedule of multi-qubit ones.

        :raises AssertionError: if the provided schedule is invalid or if the auto-scheduling is
            impossible.
        """
        ScheduledCircuit._check_input_schedule_validity(multi_qubit_moment_schedule)

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

        assert (
            _NOT_SCHEDULED not in final_schedule
        ), "Not all gates have been scheduled!"
        return ScheduledCircuit(circuit, final_schedule)

    @property
    def schedule(self) -> list[int]:
        return self._schedule

    @schedule.setter
    def schedule(self, new_schedule: list[int]) -> None:
        ScheduledCircuit._check_input_schedule_validity(new_schedule)
        number_of_moments_to_schedule: int = self._number_of_non_virtual_moments
        number_of_scheduled_moment: int = len(new_schedule)
        assert number_of_moments_to_schedule == number_of_scheduled_moment, (
            "Trying to change the underlying schedule (containing "
            f"{number_of_scheduled_moment} entries) of a ScheduledCircuit "
            "with a schedule containing a different number of "
            f"entries ({number_of_moments_to_schedule})."
        )
        self._schedule = new_schedule

    @property
    def raw_circuit(self) -> cirq.Circuit:
        return self._raw_circuit

    @raw_circuit.setter
    def raw_circuit(self, new_circuit: cirq.Circuit) -> None:
        number_of_non_virtual_moments_in_new_circuit: int = (
            ScheduledCircuit._compute_number_of_non_virtual_moments(new_circuit)
        )
        number_of_scheduled_moment: int = len(self._schedule)
        assert (
            number_of_non_virtual_moments_in_new_circuit == number_of_scheduled_moment
        ), (
            "Trying to change the underlying cirq.Circuit instance "
            f"({number_of_scheduled_moment} moments) of a ScheduledCircuit "
            "with a cirq.Circuit instance containing a different number of "
            f"moments ({number_of_non_virtual_moments_in_new_circuit})."
        )
        self._raw_circuit = new_circuit

    def map_to_qubits(
        self, qubit_map: dict[cirq.Qid, cirq.Qid], inplace: bool = False
    ) -> "ScheduledCircuit":
        """Map the qubits the ScheduledCircuit instance is applied on.

        This method forwards most of its logic to the underlying raw_circuit
        map_operations method, but additionnally takes care of forwarding tags,
        changing measurements key by re-creating the correct measurements and
        re-creating DetectorGate instances correctly.

        :param qubit_map: the map used to modify the qubits.
        :param inplace: if True, perform the modification in place and return
            self. Else, perform the modification in a copy and return the copy.

        :returns: a modified instance of ScheduledCircuit (a copy if inplace is
            True, else self).
        """

        def remap_qubits(op: cirq.Operation) -> cirq.Operation:
            op = op.transform_qubits(qubit_map)
            if isinstance(op.gate, cirq.MeasurementGate):
                return cirq.measure(*op.qubits).with_tags(*op.tags)
            elif isinstance(op.gate, DetectorGate):
                # Re-create the operation from the gate
                detector_gate: DetectorGate = deepcopy(op.gate)
                return detector_gate.on(*op.qubits, add_virtual_tag=False).with_tags(
                    *op.tags
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
        qubits = self._raw_circuit.all_qubits()
        assert all(isinstance(q, cirq.GridQubit) for q in qubits)
        return qubits  # type: ignore

    @property
    def number_of_non_virtual_moments(self) -> int:
        return self._number_of_non_virtual_moments

    @staticmethod
    def _is_virtual_moment(moment: cirq.Moment) -> bool:
        _virtual_tag = cirq.VirtualTag()
        return any(_virtual_tag in op.tags for op in moment.operations)

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

        :param circuits: the instances that should be managed.
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

        :raises AssertionError: if not self.has_pending_operation(index).
        """
        ret = self._current_moments[index]
        assert ret is not None, "No moment to pop!"
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

        :returns: a list of Moment instances that should be added next to the QEC circuit.
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

    :returns: a list containing a copy of the cirq.Operation instances from
        the given operations, without the mergeable tag, and with mergeable
        duplicates removed from the list.
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

    :returns: a circuit representing the merged scheduled circuits given as
        input.
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
