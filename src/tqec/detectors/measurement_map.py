import cirq

from tqec.exceptions import TQECException
from tqec.detectors.operation import RelativeMeasurementsRecord


def flatten(obj: cirq.Moment | cirq.AbstractCircuit) -> cirq.Circuit:
    # From https://github.com/quantumlib/Cirq/issues/3783
    if isinstance(obj, cirq.Moment):
        flattenable = [op for op in obj if isinstance(op, cirq.CircuitOperation)]
        if not flattenable:
            return cirq.Circuit(obj)
        return cirq.Circuit.zip(
            cirq.Circuit(obj - flattenable),
            *[flatten(e.mapped_circuit(True)) for e in flattenable],
        )
    return cirq.Circuit([moment for e in obj for moment in flatten(e)])


class CircuitMeasurementMap:
    def __init__(self, circuit: cirq.AbstractCircuit) -> None:
        """Stores information about all the measurements found in the provided circuit

        This class provides a method to recover the global record offset of a given
        measurement from local information about this measurement.

        :param circuit: the circuit instance to analyse.
        """
        flattened_circuit = flatten(circuit)
        (
            global_measurement_indices,
            _,
        ) = CircuitMeasurementMap._get_global_measurement_index(flattened_circuit)
        self._global_measurement_indices = global_measurement_indices

    def get_measurement_relative_offset(
        self, current_moment_index: int, qubit: cirq.Qid, measurement_offset: int
    ) -> int | None:
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
            current_moment_index, or None if the searched offset does not exist.

        :raises PositiveMeasurementOffsetError: if the provided measurement_offset value is positive.
        """
        if measurement_offset >= 0:
            raise TQECException(
                f"Found a positive measurement offset ({measurement_offset}). "
                "All measurement offsets should be strictly negative integers."
            )

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
        return None

    def _get_index_of_last_performed_measurement(
        self, current_moment_index: int
    ) -> int:
        for moment_index in reversed(range(current_moment_index + 1)):
            measurements_in_moment = self._global_measurement_indices[moment_index]
            if measurements_in_moment:
                return max(measurements_in_moment.values())
        raise TQECException(
            f"Cannot find any measurement performed before moment {current_moment_index}."
        )

    @staticmethod
    def _get_global_measurement_index(
        circuit: cirq.AbstractCircuit,
        _measurement_offset: int = 0,
    ) -> tuple[list[dict[cirq.Qid, int]], int]:
        """Computes and returns the global measurement indices for the given circuit

        This method API takes into account the fact that some information need to be passed
        across recursions and so is not really user-friendly.

        The provided circuit should not contain any cirq.CircuitOperation instance.

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
        :raises MeasurementAppliedOnMultipleQubits: if the provided cirq.AbstractCircuit instance contains
            measurements applied on several qubits at the same time.
        """
        global_measurement_indices: list[dict[cirq.Qid, int]] = []
        global_measurement_index: int = _measurement_offset
        for moment in circuit:
            global_measurement_indices.append(dict())
            for op in moment.operations:
                if isinstance(op.gate, cirq.MeasurementGate):
                    if len(op.qubits) > 1:
                        raise TQECException(f"Found a measurement applied on multiple qubits ({op.qubits}).")
                    qubit: cirq.Qid = op.qubits[0]
                    global_measurement_indices[-1][qubit] = global_measurement_index
                    global_measurement_index += 1

        return global_measurement_indices, global_measurement_index


def compute_global_measurements_lookback_offsets(
    relative_measurements_record: RelativeMeasurementsRecord,
    measurement_map: CircuitMeasurementMap,
    current_moment_index: int,
) -> list[int]:
    """Computes, from the data in the given measurement_map, the global measurement offsets

    This method uses the global data computed in the CircuitMeasurementMap instance given as
    parameter to compute the measurement record indices for the current gate instance.

    :param relative_measurements_record: the record of relative measurements to compute global
        measurements offset from.
    :param measurement_map: global measurement data obtained from the complete quantum circuit.
    :param current_moment_index: index of the moment this gate instance is found in. Used to
        recover the correct data from the given measurement_map.

    :return: the computed list of global measurements lookback offsets.
    """
    global_measurements_lookback_offsets = []
    origin = relative_measurements_record.origin
    for relative_measurement in relative_measurements_record.data:
        # Coordinate system: adding 2 GridQubit instances together, both are using the GridQubit
        #                    coordinate system, so no issue here.
        qubit = origin + relative_measurement.relative_qubit_positioning
        relative_measurement_offset = relative_measurement.relative_measurement_offset
        relative_offset = measurement_map.get_measurement_relative_offset(
            current_moment_index,
            qubit,
            relative_measurement_offset,
        )
        if relative_offset is None:
            raise TQECException(
                "An error happened during the measurement offset lookback computation. "
                f"You asked for the {relative_measurement_offset} measurement on {qubit} "
                f"at the moment {current_moment_index}. The computed measurement map is"
                f"{measurement_map}."
            )
        global_measurements_lookback_offsets.append(relative_offset)
    return global_measurements_lookback_offsets
