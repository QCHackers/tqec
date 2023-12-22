from copy import deepcopy

import cirq
import numpy
import stim

from tqec.detectors.measurement_map import CircuitMeasurementMap


class ShiftCoordsGate(cirq.Gate):
    def __init__(self, *args: int) -> None:
        self._args = args

    def _num_qubits_(self):
        # Set to 1 to avoid any issue with a 0-qubit "gate".
        return 1

    def _unitary_(self):
        # Set to the identity as this is not really a gate.
        return numpy.array([[1, 0], [0, 1]], dtype=float)

    def on(self, *qubits: cirq.Qid) -> cirq.Operation:
        # Add the virtual tag to explicitely mark this gate as "not a real gate"
        return super().on(*qubits).with_tags(cirq.VirtualTag())

    def _circuit_diagram_info_(self, _: cirq.CircuitDiagramInfoArgs):
        targets = ",".join(map(str, self._args))
        return f"SC({targets})"

    def _stim_conversion_(
        self,
        # The stim circuit being built. Add onto it.
        edit_circuit: stim.Circuit,
        # Metadata about measurement groupings needed by stimcirq.StimSampler.
        # If your gate contains a measurement, it has to append how many qubits
        # that measurement measures (and its key) into this list.
        edit_measurement_key_lengths: list[tuple[str, int]],
        # The indices of qubits the gate is operating on.
        targets: list[int],
        # Forward compatibility with future arguments.
        **_,
    ):
        edit_circuit.append("SHIFT_COORDS", [], self._args)


class DetectorGate(cirq.Gate):
    def __init__(
        self,
        qubit_coordinate_system_origin: cirq.GridQubit,
        measurements_loopback_offsets: list[tuple[cirq.GridQubit, int]],
        time_coordinate: int = 0,
    ) -> None:
        """Gate representing a detector.

        Issue with this class: cirq expectations for a subclass of cirq.Gate is the following (from cirq
        documentation https://quantumai.google/cirq/build/gates):

        > A Gate is an effect that can be applied to a collection of qubits (objects with a Qid).
        > Gates can be applied to qubits by calling their on method, or, alternatively calling the gate
        > on the qubits. The object created by such calls is an Operation. Alternatively, a Gate can be
        > thought of as a factory that, given input qubits, generates an associated GateOperation object.

        I understand that as "cirq.Gate instances should not have any qubit-specific knowledge as this is the
        role of the cirq.Operation class".
        And this is fine in theory as a DetectorGate should only store:
        - a time coordinate
        - offsets from the origin qubit (origin qubit that should be provided with the "on" method to
          create an instance of cirq.Operation).

        Resolving measurement offsets could be done inside the _stim_conversion_ method thanks to:
        - the fact that qubit coordinates can be recovered with stim.Circuit.get_final_qubit_coordinates,
        - the fact that detectors only reference past measurements, already in the stim.Circuit instance.

        But the second point above is not always true: if a repetition is found (i.e., stim.CircuitRepeatBlock),
        the stim.Circuit instance given to the _stim_conversion_ method is bounded to the stim.Circuit instance
        in the stim.CircuitRepeatBlock and has no way of accessing the parent stim.Circuit instance.
        This makes impossible to reliably compute measurement offsets, **even by considering that the measurement
        schedule in the repeat-block is consistent with the one just before the repeat block**.
        One solution to that would be to give access to parent stim.Circuit instances, that should be doable but
        requires a change directly in Stim.

        :param qubit_coordinate_system_origin: origin of the qubit coordinate system. Used to move detectors
            along with measurement gates.
        :param measurements_loopback_offsets: a list of measurements that are part of the detector. The
            measurements are given as a tuple with the following entries:

            1. a qubit offset, that is considered relative to the qubit this gate will be applied on, and that
               represent the qubit the measurement we want to access has been performed on,
            2. a **local**, **negative** offset, representing the n-th measurement on the qubit given in the
               first entry of the tuple, going backward **from the predecessor of the Moment containing this
               gate** (this is where the **local** comes from).

            The tuple [cirq.GridQubit(1, 1), -1] means the last measurement that is:
            1. located before the Moment this gate is in, and
            2. applied on the qubit "origin + cirq.GridQubit(1, 1)", where "origin" is the qubit given to
               the "on" method to construct an operation.
        :param time_coordinate: an annotation that will be forwarded to the DETECTOR Stim structure as the
            last coordinate.
        """
        self._qubit_coordinate_system_origin = qubit_coordinate_system_origin
        self._local_measurements_loopback_offsets_relative_to_origin = [
            (qubit - qubit_coordinate_system_origin, offset)
            for qubit, offset in measurements_loopback_offsets
        ]
        self._global_measurements_loopback_offsets: list[int] = []
        self._time_coordinate = time_coordinate
        super().__init__()

    def __deepcopy__(self, memo: dict) -> "DetectorGate":
        return DetectorGate(
            deepcopy(self._qubit_coordinate_system_origin, memo=memo),
            [
                (qubit + self._qubit_coordinate_system_origin, offset)
                for qubit, offset in self._local_measurements_loopback_offsets_relative_to_origin
            ],
            self._time_coordinate,
        )

    def __copy__(self) -> "DetectorGate":
        # Force the deepcopy to avoid any issue from shared reference. This is a safety measure to mitigate
        # potential issues caused by the fact that this class does not follow the spirit of cirq.Gate interface.
        return self.__deepcopy__({})

    def _num_qubits_(self):
        return 1

    def _unitary_(self):
        return numpy.array([[1, 0], [0, 1]], dtype=float)

    def _circuit_diagram_info_(self, _: cirq.CircuitDiagramInfoArgs):
        return "D"

    @property
    def coordinates(self) -> tuple[int, ...]:
        return (
            self._qubit_coordinate_system_origin.row,
            self._qubit_coordinate_system_origin.col,
            self._time_coordinate,
        )

    def on(self, *qubits: cirq.Qid, add_virtual_tag: bool = True) -> cirq.Operation:
        # Add the virtual tag to explicitely mark this gate as "not a real gate"
        assert len(qubits) == 1, (
            f"Cannot apply a {self.__class__.__name__} to more than "
            f"1 qubits ({len(qubits)} qubits given)."
        )
        assert isinstance(qubits[0], cirq.GridQubit), "Expecting a GridQubit instance."
        self._set_origin(qubits[0])
        tag = [cirq.VirtualTag()] if add_virtual_tag else []
        return super().on(*qubits).with_tags(*tag)

    def _set_origin(self, new_origin: cirq.GridQubit) -> None:
        self._qubit_coordinate_system_origin = new_origin

    def _stim_conversion_(
        self,
        # The stim circuit being built. Add onto it.
        edit_circuit: stim.Circuit,
        # Metadata about measurement groupings needed by stimcirq.StimSampler.
        # If your gate contains a measurement, it has to append how many qubits
        # that measurement measures (and its key) into this list.
        edit_measurement_key_lengths: list[tuple[str, int]],
        # The indices of qubits the gate is operating on.
        targets: list[int],
        # Forward compatibility with future arguments.
        **_,
    ):
        assert self._global_measurements_loopback_offsets, (
            "Global measurement loopback offsets have not been computed."
            " Please call compute_global_measurements_loopback_offsets."
        )
        edit_circuit.append(
            "DETECTOR",
            [stim.target_rec(i) for i in self._global_measurements_loopback_offsets],
            self.coordinates,
        )

    def compute_global_measurements_loopback_offsets(
        self,
        measurement_map: CircuitMeasurementMap,
        current_moment_index: int,
    ) -> None:
        self._global_measurements_loopback_offsets.clear()
        for (
            qubit_offset,
            loopback_offset,
        ) in self._local_measurements_loopback_offsets_relative_to_origin:
            qubit = self._qubit_coordinate_system_origin + qubit_offset
            self._global_measurements_loopback_offsets.append(
                measurement_map.get_measurement_relative_offset(
                    current_moment_index, qubit, loopback_offset
                )
            )
