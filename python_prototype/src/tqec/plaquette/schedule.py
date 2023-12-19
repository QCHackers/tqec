from cirq.circuits.circuit import Circuit
from cirq.ops.raw_types import Qid, Operation
from cirq.circuits.moment import Moment
import cirq


class ScheduledCircuit:
    def __init__(self, circuit: Circuit, schedule: list[int] | None = None) -> None:
        """Represent a quantum circuit with scheduled multi-qubit gates.

        This class aims at representing a Circuit instance that has all its multi-qubit
        gates scheduled, i.e., associated with a time slice.

        :param circuit: the instance of Circuit that is scheduled.
        :param schedule: a sorted list of time slices indices. The list should contain
            as much indices as there are multi-qubit gates in the provided Circuit instance.
            If the list is None, it default to list(range(number_of_multi_qubit_gates)).

        :raises AssertionError: if the indices in the schedule list are not sorted.
        :raises AssertionError: if the number of provided indices in the schedule list does
            not match exactly with the number of multi-qubit gates in the circuit.
        """
        number_of_gates_to_schedule: int = sum(
            len(op.qubits) > 1 for op in circuit.all_operations()
        )
        if schedule is None:
            schedule = list(range(number_of_gates_to_schedule))
        else:
            assert len(schedule) == number_of_gates_to_schedule, (
                f"Cannot create a ScheduledCircuit instance with a different number "
                f"of multi-qubit gates ({number_of_gates_to_schedule}) and time slices "
                f"in the provided schedule ({len(schedule)})."
            )
        assert all(
            schedule[i] <= schedule[i + 1] for i in range(len(schedule) - 1)
        ), "Given schedule should be a sorted list of integers."

        self._raw_circuit = circuit
        self._schedule = schedule

    @property
    def schedule(self) -> list[int]:
        return self._schedule

    @property
    def raw_circuit(self) -> Circuit:
        return self._raw_circuit

    @raw_circuit.setter
    def raw_circuit(self, other: Circuit) -> None:
        self._raw_circuit = other

    def map_to_qubits(
        self, qubit_map: dict[Qid, Qid], inplace: bool = False
    ) -> "ScheduledCircuit":
        """Map the qubits the ScheduledCircuit instance is applied on.

        This method forwards most of its logic to the underlying raw_circuit
        map_operations method, but additionnally takes care of forwarding tags
        and changing measurements key by re-creating the correct measurements.

        :param qubit_map: the map used to modify the qubits.
        :param inplace: if True, perform the modification in place and return
            self. Else, perform the modification in a copy and return the copy.

        :returns: a modified instance of ScheduledCircuit (a copy if inplace is
            True, else self).
        """

        def remap_qubits(op: Operation) -> Operation:
            op = op.transform_qubits(qubit_map)
            if isinstance(op.gate, cirq.MeasurementGate):
                return cirq.measure(*op.qubits).with_tags(*op.tags)
            else:
                return op

        operand = self if inplace else self.copy()
        operand.raw_circuit = operand.raw_circuit.map_operations(remap_qubits)
        return operand

    def copy(self) -> "ScheduledCircuit":
        return ScheduledCircuit(
            self._raw_circuit.copy(),
            self._schedule.copy(),
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
        self._iterators = [
            circuit.raw_circuit.all_operations() for circuit in self._circuits
        ]
        self._current_operations = [next(it, None) for it in self._iterators]
        self._number_of_multi_qubit_operations_poped: list[int] = [0 for _ in circuits]

    def has_pending_operation(self) -> bool:
        """Checks if any of the managed instances has a pending operation.

        Any operation that has not been collected by using either collect_1q_operations or
        collect_multi_qubit_gates_with_same_schedule is considered to be pending.
        """
        return any(self._has_operation(i) for i in range(len(self._circuits)))

    def has_multi_qubit_operation_ready_to_be_collected(self) -> bool:
        """Checks if any of the managed instances has a mutli-qubit operation ready to be executed."""

        def is_multi_qubit_operation(op: Operation | None) -> bool:
            return op is not None and len(op.qubits) > 1

        return any(
            is_multi_qubit_operation(self._peek_operation(i))
            for i in range(len(self._circuits))
        )

    def _has_operation(self, index: int) -> bool:
        """Check if the managed instance at the given index has a pending operation."""
        return self._current_operations[index] is not None

    def _peek_operation(self, index: int) -> Operation | None:
        """Recover **without collecting** the pending operation for the instance at the given index."""
        return self._current_operations[index]

    def _pop_operation(self, index: int) -> Operation:
        """Recover and mark as collected the pending operation for the instance at the given index.

        :raises AssertionError: if not self.has_pending_operation(index).
        """
        ret = self._current_operations[index]
        assert ret is not None, "No operation to pop!"
        self._current_operations[index] = next(self._iterators[index], None)
        self._number_of_multi_qubit_operations_poped[index] += len(ret.qubits) > 1
        return ret

    def collect_1q_operations(
        self, avoided_gate_types: set[type] | None = None
    ) -> list[Operation]:
        """Collect all the 1-qubit operations that can be collected.

        This method collects and returns a list of all the 1-qubit operations that can
        be eagerly collected. It stops when there is no 1-qubit operation left pending,
        either because the managed circuits have no more pending operation or because the
        only pending operations are multi-qubit gates.

        :returns: a list of 1-qubit operations that are not measurements.
        """
        if avoided_gate_types is None:
            avoided_gate_types = set()
        operations: list[Operation] = list()
        for circuit_index in range(len(self._circuits)):
            while (
                self._has_operation(circuit_index)
                and len(self._peek_operation(circuit_index).qubits) == 1
                and all(
                    not isinstance(self._peek_operation(circuit_index).gate, gate_type)
                    for gate_type in avoided_gate_types
                )
            ):
                operations.append(self._pop_operation(circuit_index))
        return operations

    def collect_specific_operations(self, gate_types: set[type]) -> list[Operation]:
        """Collect all the 1-qubit operations that can be collected.

        This method collects and returns a list of all the 1-qubit operations that can
        be eagerly collected. It stops when there is no 1-qubit operation left pending,
        either because the managed circuits have no more pending operation or because the
        only pending operations are multi-qubit gates.

        :returns: a list of 1-qubit measurement operations.
        """
        operations: list[Operation] = list()
        for circuit_index in range(len(self._circuits)):
            while (
                self._has_operation(circuit_index)
                and len(self._peek_operation(circuit_index).qubits) == 1
                and any(
                    isinstance(self._peek_operation(circuit_index).gate, gate_type)
                    for gate_type in gate_types
                )
            ):
                operations.append(self._pop_operation(circuit_index))
        return operations

    def collect_multi_qubit_gates_with_same_schedule(self) -> list[Operation]:
        """Collect all the multi-qubit operations that can be collected.

        This method collects and returns a list of all the multi-qubit operations that can
        be eagerly collected. It stops when there is no multi-qubit operation left pending,
        either because the managed circuits have no more pending operation or because the
        only pending operations are 1-qubit gates.

        :returns: a list of multi-qubit operations.
        """
        schedules: dict[int, list[int]] = dict()
        for circuit_index, scheduled_circuit in enumerate(self._circuits):
            if not self._has_operation(circuit_index):
                continue
            current_operation = self._peek_operation(circuit_index)
            operation_qubit_number = len(current_operation.qubits)
            if operation_qubit_number <= 1:
                continue
            scheduled_time = scheduled_circuit.schedule[
                self._number_of_multi_qubit_operations_poped[circuit_index]
            ]
            schedules.setdefault(scheduled_time, list()).append(circuit_index)
        # It is possible that no multi-qubit gate is ready to be collected. In this case,
        # schedules is empty.
        if not schedules:
            return []
        first_schedule: int = min(schedules.keys())
        return [
            self._pop_operation(circuit_index)
            for circuit_index in schedules[first_schedule]
        ]


def remove_duplicate_operations(
    operations: list[cirq.Operation],
) -> list[cirq.Operation]:
    # Import needed here to resolve at runtime and avoid circular import.
    from tqec.plaquette.plaquette import Plaquette

    mergeable_operations: list[cirq.Operation] = list()
    final_operations: list[cirq.Operation] = list()
    for operation in operations:
        if Plaquette._MERGEABLE_TAG in operation.tags:
            mergeable_operations.append(operation)
        else:
            final_operations.append(operation)
    # Remove mergeable measurements with the set data-structure
    for merged_operation in set(mergeable_operations):
        tags = set(merged_operation.tags)
        if Plaquette._MERGEABLE_TAG in tags:
            tags.remove(Plaquette._MERGEABLE_TAG)
        final_operations.append(merged_operation.untagged.with_tags(*tags))
    return final_operations


def merge_scheduled_circuits(circuits: list[ScheduledCircuit]) -> Circuit:
    scheduled_circuits = ScheduledCircuits(circuits)

    # Collect and remove duplicates for the initial reset operations
    reset_operations = remove_duplicate_operations(
        scheduled_circuits.collect_specific_operations({cirq.ResetChannel})
    )
    # Merge the initial 1-qubit operations.
    one_qubit_operations = scheduled_circuits.collect_1q_operations(
        avoided_gate_types={cirq.MeasurementGate}
    )
    initial_one_qubit_operations_circuit = Circuit()
    initial_one_qubit_operations_circuit.append(one_qubit_operations)

    multi_qubit_operations_circuit = Circuit()
    while scheduled_circuits.has_multi_qubit_operation_ready_to_be_collected():
        multi_qubit_gates = (
            scheduled_circuits.collect_multi_qubit_gates_with_same_schedule()
        )
        # Explicitely use a Moment to avoid overlapping gates.
        multi_qubit_operations_circuit.append(Moment(*multi_qubit_gates))

    # Merge the final 1-qubit operations.
    one_qubit_operations = scheduled_circuits.collect_1q_operations(
        avoided_gate_types={cirq.MeasurementGate}
    )
    final_one_qubit_operations_circuit = Circuit()
    final_one_qubit_operations_circuit.append(one_qubit_operations)
    final_one_qubit_operations_circuit = cirq.align_right(
        final_one_qubit_operations_circuit
    )

    # Removing duplicate measurements by using the set data-structure.
    final_measurement_operations = remove_duplicate_operations(
        scheduled_circuits.collect_specific_operations(
            gate_types={cirq.MeasurementGate}
        )
    )
    # Sorting measurements according to the order on the qubits they are applied on.
    assert all(
        len(op.qubits) == 1 for op in final_measurement_operations
    ), "Found a measurement that is not applied on exactly 1 qubit."
    final_measurement_operations.sort(key=lambda op: op.qubits[0])
    assert not scheduled_circuits.has_pending_operation(), (
        "For the moment, ScheduledCircuit instances should be composed of "
        "1) layer(s) of 1-qubit gates, 2) layer(s) of multi-qubit gates and "
        "3) layer(s) of 1-qubit gate. Any other circuit is considered invalid"
    )

    return (
        reset_operations
        + initial_one_qubit_operations_circuit
        + multi_qubit_operations_circuit
        + final_one_qubit_operations_circuit
        + final_measurement_operations
    )
