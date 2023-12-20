import cirq
from cirq.ops.raw_types import Operation, Qid
import stim
import numpy
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

    def on(self, *qubits: Qid) -> Operation:
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
        **kwargs,
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

        :param qubit_coordinate_system_origin: origin of the qubit coordinate system. Used to move detectors
            along with measurement gates.
        :param measurements_loopback_offsets: a list of measurements that are part of the detector. The
            measurements are given as a tuple with the following entries:

            1. the qubit the measurement we want to access has been performed on,
            2. a **local**, **negative** offset, representing the n-th measurement on the qubit given in the
               first entry of the tuple, going backward **from the predecessor of the Moment containing this
               gate** (this is where the **local** comes from).

            The tuple [cirq.GridQubit(1, 1), -1] means the last measurement that is:
            1. located before the Moment this gate is in, and
            2. applied on the cirq.GridQubit(1, 1) qubit.
        :param time_coordinate: an annotation that will be forwarded to the DETECTOR Stim structure as the
            last coordinate.
        """
        self._origin = qubit_coordinate_system_origin
        self._local_measurements_loopback_offsets_relative_to_origin = [
            (qubit - self._origin, loopback_offset)
            for qubit, loopback_offset in measurements_loopback_offsets
        ]
        self._global_measurements_loopback_offsets: list[int] = []
        self._time_coordinate = time_coordinate
        self._coordinates: list[int] = []
        super().__init__()

    def _num_qubits_(self):
        return 1

    def _unitary_(self):
        return numpy.array([[1, 0], [0, 1]], dtype=float)

    def _circuit_diagram_info_(self, _: cirq.CircuitDiagramInfoArgs):
        if self._coordinates:
            return f"D({','.join(map(str, self._coordinates))})"
        else:
            return "D"

    def _set_origin(self, new_origin: cirq.GridQubit) -> None:
        self._origin = new_origin
        self._set_coordinates(new_origin)

    def _set_coordinates(self, qubit: cirq.GridQubit) -> None:
        self._coordinates = [qubit.row, qubit.col, self._time_coordinate]

    def on(self, *qubits: cirq.GridQubit, add_virtual_tag: bool = True) -> Operation:
        # Add the virtual tag to explicitely mark this gate as "not a real gate"
        assert (
            len(qubits) == 1
        ), f"Cannot apply a {self.__class__.__name__} to more than 1 qubits ({len(qubits)} given)."
        self._set_origin(qubits[0])
        tag = [cirq.VirtualTag()] if add_virtual_tag else []
        return super().on(*qubits).with_tags(*tag)

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
        **kwargs,
    ):
        assert self._global_measurements_loopback_offsets, (
            "Global measurement loopback offsets have not been computed."
            " Please call compute_global_measurements_loopback_offsets."
        )
        edit_circuit.append(
            "DETECTOR",
            [stim.target_rec(i) for i in self._global_measurements_loopback_offsets],
            self._coordinates,
        )

    def compute_global_measurements_loopback_offsets(
        self, measurement_map: CircuitMeasurementMap, current_moment_index: int
    ) -> None:
        self._global_measurements_loopback_offsets.clear()
        for (
            qubit_offset,
            loopback_offset,
        ) in self._local_measurements_loopback_offsets_relative_to_origin:
            qubit = self._origin + qubit_offset
            self._global_measurements_loopback_offsets.append(
                measurement_map.get_measurement_relative_offset(
                    current_moment_index, qubit, loopback_offset
                )
            )
