import cirq


class CircuitMeasurementMap:
    def __init__(self, circuit: cirq.AbstractCircuit) -> None:
        (
            global_measurement_indices,
            number_of_moments,
        ) = CircuitMeasurementMap._get_global_measurement_index(circuit)
        self._global_measurement_indices = global_measurement_indices

    def get_measurement_relative_offset(
        self, current_moment_index: int, qubit: cirq.Qid, qubit_offset: int
    ) -> int:
        assert qubit_offset < 0, "qubit_offset is expected to be stricly negative."
        last_performed_measurement = self._get_index_of_last_performed_measurement(
            current_moment_index
        )
        seen_measurements_on_qubit: int = 0
        # We do not take into account the current moment, so we start at the moment
        # just before.
        for moment_index in reversed(range(current_moment_index)):
            moment_has_measurement_on_qubit: bool = (
                qubit in self._global_measurement_indices[moment_index]
            )
            if moment_has_measurement_on_qubit:
                seen_measurements_on_qubit += 1
            if seen_measurements_on_qubit == -qubit_offset:
                return -1 - (
                    last_performed_measurement
                    - self._global_measurement_indices[moment_index][qubit]
                )
        assert False, "Cannot find measurement relative offset."

    def _get_index_of_last_performed_measurement(
        self, current_moment_index: int
    ) -> int:
        for moment_index in reversed(range(current_moment_index + 1)):
            measurements_in_moment = self._global_measurement_indices[moment_index]
            if measurements_in_moment:
                return max(measurements_in_moment.values())
        assert (
            False
        ), f"Cannot find any measurements in or before the {current_moment_index}-th moment."

    @staticmethod
    def _get_global_measurement_index(
        circuit: cirq.AbstractCircuit,
        measurement_offset: int = 0,
    ) -> tuple[list[dict[cirq.Qid, int]], int]:
        global_measurement_indices: list[dict[cirq.Qid, int]] = []
        global_measurement_index: int = measurement_offset
        for moment in circuit:
            global_measurement_indices.append(dict())
            moment_contains_measurement: bool = False
            moment_contains_CircuitOperation: bool = False
            for op in moment.operations:
                if isinstance(op.gate, cirq.MeasurementGate):
                    assert (
                        len(op.qubits) == 1
                    ), "Measurement gates should only be applied on 1 qubit."
                    moment_contains_measurement = True
                    qubit: cirq.Qid = op.qubits[0]
                    global_measurement_indices[-1][qubit] = global_measurement_index
                    global_measurement_index += 1
                elif isinstance(op, cirq.CircuitOperation):
                    # Assumptions:
                    # 1. this operation is the only one that contains measurements in the Moment instance.
                    #    This assumption is checked and asserted in this function, so we can consider it valid.
                    # 2. the op.circuit extracted in the next line of code has the same measurement
                    #    patterns as the previous analysed moments. This is required as:
                    #    - the use of CircuitOperation instances is likely to be able to represent a repeated
                    #      circuit, to perform several rounds of error correction.
                    #    - for rounds of error correction, the first iteration of the repeated part will
                    #      reference measurements that happened in the previous, non-repeated, part of the circuit
                    #      whereas all the other repetitions will reference measurements from the previous repetitions.
                    #      In order for that to be valid, a certain consistency is expected between the measurements
                    #      performed in a repeated portion and the ones performed just before.
                    #    This assumption is likely a requirement for a QEC code to be considered valid, but it does
                    #    not hurt to make that explicit for the moment.
                    # The second assumption is not checkable easily here, so let's hope that it is valid,
                    # and change this code portion for something more robust when possible.
                    moment_contains_CircuitOperation = True
                    (
                        indices,
                        new_global_measurement_index,
                    ) = CircuitMeasurementMap._get_global_measurement_index(
                        op.circuit, global_measurement_index
                    )
                    global_measurement_index = new_global_measurement_index
                    # remove the last entry of global_measurement_indices (that should be empty if
                    # assumption 1 is valid).
                    assert not global_measurement_indices[
                        -1
                    ], "Attempting to pop a non-empty measurement map."
                    global_measurement_indices.pop()
                    global_measurement_indices.extend(indices)
            # Check assumption 1 of the CircuitOperation branch.
            assert not (
                moment_contains_measurement and moment_contains_CircuitOperation
            ), (
                "Found a Moment instance that contains both a MeasurementGate and a "
                "CircuitOperation. This breaks an assumption, results will be invalid."
            )
        return global_measurement_indices, global_measurement_index
