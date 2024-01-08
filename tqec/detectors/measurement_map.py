import cirq


class CircuitMeasurementMap:
    def __init__(self, circuit: cirq.AbstractCircuit) -> None:
        """Stores information about all the measurements found in the provided circuit

        This class provides a method to recover the global record offset of a given
        measurement from local informations about this measurement.

        :param circuit: the circuit instance to analyse.
        """
        (
            global_measurement_indices,
            _,
        ) = CircuitMeasurementMap._get_global_measurement_index(circuit)
        self._global_measurement_indices = global_measurement_indices

    def get_measurement_relative_offset(
        self, current_moment_index: int, qubit: cirq.Qid, measurement_offset: int
    ) -> int:
        """Recover the record offset of the given local measurement description

        This is the main method of CircuitMeasurementMap. It allows to query for measurements
        with their local temporal description and to recover the global offset that should be
        used to get the measurement result from the global measurement record.

        :param current_moment_index: the moment index for which we want to compute the offset.
            This method will only backtrack in time, and so will never return measurements that
            are performed after the moment provided in this parameter. Also, the measurement
            record offset is a local quantity that might change in time (due to subsequent
            measurements shifting the offset), meaning that the returned offset should only be
            considered valid for the moment provided here, and for no other moments.
        :param qubit: qubit instance the measurement we are searching for has been performed on.
        :param measurement_offset: the temporally-local, negative, measurement offset. A value of
            -1 means "the last measurement performed on this qubit" ("last" should always be read
            as "last from the current_moment_index moment view"), -2 means "the measurement just
            before the last measurement performed on this qubit", etc.
        :returns: the global measurement record offset, only valid for the provided
            current_moment_index.
        """
        assert (
            measurement_offset < 0
        ), "measurement_offset is expected to be stricly negative."
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
            if seen_measurements_on_qubit == -measurement_offset:
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
        assert False, f"Cannot find any measurements in or before the {current_moment_index}-th moment."

    @staticmethod
    def _get_global_measurement_index(
        circuit: cirq.AbstractCircuit,
        _measurement_offset: int = 0,
    ) -> tuple[list[dict[cirq.Qid, int]], int]:
        """Computes and returns the global measurement indices for the given circuit

        This method API takes into account the fact that some information need to be passed
        accross recursions and so is not really user-friendly.

        Measurements in repeated cirq.CircuitOperation instances are only counted once, contributing
        to the global indexing only once.

        If the given circuit contains at least one cirq.CircuitOperation instance, the following
        pre-condition should be met for this method to output a correct result:

        1. If a cirq.CircuitOperation instance is present in a given Moment, it is the only operation
           that contains measurements in this Moment.
           This assumption is asserted in this method, so failing to check it will raise an AssertionError.
        2. If a cirq.CircuitOperation instance is present in a given Moment, it contains a
           cirq.AbstractCircuit instance that has a measurement schedule **compatible** with the Moment
           instances preceding it.
           This is required as:
           - the use of CircuitOperation instances is often used to represent a repeated circuit, to
             perform several rounds of error correction.
           - for rounds of error correction, the first iteration of the repeated part will reference
             measurements that happened in the previous, non-repeated, part of the circuit whereas all
             the subsequent repetitions will reference measurements from earlier repetitions of the
             same circuit. In order for that scheme to be valid, a certain consistency is expected
             between the measurements performed in a repeated portion and the ones performed just before.
             This assumption is likely a requirement for any QEC code with repeated rounds to be
             considered valid, but it does not hurt to make that explicit for the moment.

        The second assumption is not checkable easily in this method and so is not checked for the moment.
        Any input circuit that fails to ensure these pre-conditions should be considered invalid input.

        :param circuit: circuit to compute the global measurements of.
        :param _measurement_offset: offset applied to the indices of each measurements. Used for the
            recursive calls.
        :returns: a tuple (global_measurement_indices, global_measurement_index).
            - global_measurement_indices is a list containing one entry for each Moment in the provided
              circuit. The entry for a given Moment corresponds to a mapping from the qubit instance that
              has been measured and the global measurement index (again, measurements in repeated
              cirq.CircuitOperation instances are only counted once).
            - global_measurement_index is an integer representing the index of the next measurement that
              will be encountered. It is part of the return API to simplify the recursion, and should not
              be useful for the external caller.
        :raises AssertionError: see pre-conditions in docstring.
        """
        global_measurement_indices: list[dict[cirq.Qid, int]] = []
        global_measurement_index: int = _measurement_offset
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
                    # See assumptions in docstring.
                    moment_contains_CircuitOperation = True
                    # Compute the measurement indices of the sub-circuit recursively.
                    (
                        indices,
                        new_global_measurement_index,
                    ) = CircuitMeasurementMap._get_global_measurement_index(
                        op.circuit, global_measurement_index
                    )
                    # Update the current measurement index, as the recursive call might have seen
                    # some measurements.
                    global_measurement_index = new_global_measurement_index
                    # Remove the last entry of global_measurement_indices (that should be empty if
                    # assumption 1 is valid, checked at the end of the for loop) and extend it with
                    # the computed indices.
                    global_measurement_indices.pop()
                    global_measurement_indices.extend(indices)
            # Check assumption 1 of the CircuitOperation branch.
            # Note that this does not check the full assumption: if there are 2 CircuitOperation
            # instances, or some MeasurementAndReset gate, this assert will not raise but the
            # output will still be invalid.
            assert not (
                moment_contains_measurement and moment_contains_CircuitOperation
            ), (
                "Found a Moment instance that contains both a MeasurementGate and a "
                "CircuitOperation. This breaks an assumption, results will be invalid."
            )
        return global_measurement_indices, global_measurement_index
