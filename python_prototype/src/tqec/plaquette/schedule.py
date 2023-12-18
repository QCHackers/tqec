from cirq.circuits.circuit import Circuit
from cirq.ops.raw_types import Qid, Operation
from cirq.circuits.moment import Moment
import cirq


class ScheduledCircuit:
    def __init__(self, circuit: Circuit, schedule: list[int] | None = None) -> None:
        number_of_gates_to_schedule: int = sum(
            len(op.qubits) > 1 for op in circuit.all_operations()
        )
        if schedule is None:
            schedule = list(range(number_of_gates_to_schedule))

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
        self._circuits = circuits
        self._iterators = [
            circuit.raw_circuit.all_operations() for circuit in self._circuits
        ]
        self._current_operations = [next(it, None) for it in self._iterators]
        self._number_of_multi_qubit_operations_poped: list[int] = [0 for _ in circuits]

    def has_pending_operation(self) -> bool:
        return any(self._has_operation(i) for i in range(len(self._circuits)))

    def has_pending_multi_qubit_operation(self) -> bool:
        def is_multi_qubit_operation(op: Operation | None) -> bool:
            return op is not None and len(op.qubits) > 1

        return any(
            is_multi_qubit_operation(self._peek_operation(i))
            for i in range(len(self._circuits))
        )

    def _has_operation(self, index: int) -> bool:
        return self._current_operations[index] is not None

    def _peek_operation(self, index: int) -> Operation | None:
        return self._current_operations[index]

    def _pop_operation(self, index: int) -> Operation:
        ret = self._current_operations[index]
        assert ret is not None, "No operation to pop!"
        self._current_operations[index] = next(self._iterators[index], None)
        self._number_of_multi_qubit_operations_poped[index] += len(ret.qubits) > 1
        return ret

    def collect_1q_operations(self) -> list[Operation]:
        operations: list[Operation] = list()
        for circuit_index in range(len(self._circuits)):
            while (
                self._has_operation(circuit_index)
                and len(self._current_operations[circuit_index].qubits) == 1
            ):
                operations.append(self._pop_operation(circuit_index))
        return operations

    def collect_multi_qubit_gates_with_same_schedule(self) -> list[Operation]:
        schedules: dict[int, list[int]] = dict()
        for circuit_index, scheduled_circuit in enumerate(self._circuits):
            if not self._has_operation(circuit_index):
                continue
            current_operation = self._current_operations[circuit_index]
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


def merge_scheduled_circuits(circuits: list[ScheduledCircuit]) -> Circuit:
    scheduled_circuits = ScheduledCircuits(circuits)
    # Merge the initial 1-qubit operations.
    one_qubit_operations = scheduled_circuits.collect_1q_operations()
    initial_one_qubit_operations_circuit = Circuit()
    initial_one_qubit_operations_circuit.append(one_qubit_operations)

    multi_qubit_operations_circuit = Circuit()
    while scheduled_circuits.has_pending_multi_qubit_operation():
        multi_qubit_gates = (
            scheduled_circuits.collect_multi_qubit_gates_with_same_schedule()
        )
        # Explicitely use a Moment to avoid overlapping gates.
        multi_qubit_operations_circuit.append(Moment(*multi_qubit_gates))

    # Merge the final 1-qubit operations.
    one_qubit_operations = scheduled_circuits.collect_1q_operations()
    final_one_qubit_operations_circuit = Circuit()
    final_one_qubit_operations_circuit.append(one_qubit_operations)
    final_one_qubit_operations_circuit = cirq.align_right(
        final_one_qubit_operations_circuit
    )
    assert not scheduled_circuits.has_pending_operation(), (
        "For the moment, ScheduledCircuit instances should be composed of "
        "1) layer(s) of 1-qubit gates, 2) layer(s) of multi-qubit gates and "
        "3) layer(s) of 1-qubit gate. Any other circuit is considered invalid"
    )

    return (
        initial_one_qubit_operations_circuit
        + multi_qubit_operations_circuit
        + final_one_qubit_operations_circuit
    )
